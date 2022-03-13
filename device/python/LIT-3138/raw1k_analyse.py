
from argparse import ArgumentParser
from enum import Enum
from datetime import datetime
from datetime import timezone
import json
import re
from matplotlib import pyplot
from matplotlib import ticker
import numpy


DAY_ZERO = 1388527200

DSP_PATTERN = re.compile("data_fill_buf_a2d: TAG_XPORT_SE_DSP_REPORT_4 \
sensor=<([0-9]{8})>flags<([0-9]{2})>seq_no<([0-9]*)>")

FUZION_DSP_PATTERN = re.compile("bio signal DSP report: version ([0-9]) \
ser_no ([0-9]) seq_no ([0-9]*) gmt_time ([0-9]*) presence ([0-9])")


class Action(Enum):
    FIND_MISSING_DSP = "find_missing_dsp"
    CMP_DSP = "cmp_dsp"


class DABFlags:
    HAVE_RAW = (1 << 0)
    HAVE_REPORT = (1 << 1)
    SENT_RAW = (1 << 2)
    SENT_REPORT = (1 << 3)

    # set when the latest raw audio sample has arrived

    HAVE_AUDIO = (1 << 4)

    # set when the latest raw audio sample has been sent to the server

    SENT_AUDIO = (1 << 5)

    # set when the latest raw audio sample has passed through the Algo wrapper

    HANDLED_AUDIO = (1 << 6)

    # set when it's time to send the HRV data. It's populated every time
    # but only sent on a bed presence transition to out

    HAVE_HRV = (1 << 7)


def ts2utc(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def missing_hist_formatter(ts, _):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M")


def prepare_raw1k(j):
    del j["header"]

    return j


def raw1k_extract_tss(j):
    tss = [f["time_stamp"] // 1000 for f in j.values()]
    tss = sorted(tss)

    return tss


def raw1k_extract_dsps(j):
    dsps = []

    for frame in j.values():
        ts = frame["time_stamp"]
        tag = "TAG_DSP_TIMESTAMP"

        if tag in frame:
            dsp_ts = frame[tag]["m_time_stamp_dsp"]
            dsp_seqn = frame["TAG_DSP_SEQ_NUM"]["m_seq_number_dsp"]

            if dsp_ts // 1000 < DAY_ZERO:
                print("invalid DSP ts {}, skipping".format(dsp_ts))

                continue

            dsps.append((ts, dsp_ts, dsp_seqn))

    return dsps


def plot_missing_hist(tss, missed_dsp, args=None, suffix=""):
    ts_range = tss[-1] - tss[0]

    missed_perc = len(missed_dsp) * 100 / ts_range
    fig, ax = pyplot.subplots(figsize=(13, 4.8))
    n, bins, _ = ax.hist(missed_dsp, 60)
    maxn = round(bins[1] - bins[0])

    ax.xaxis.set_tick_params(which="major", labelsize=4, labelrotation=90)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(200))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(missing_hist_formatter))
    ax.set_xlim(tss[0], tss[-1])
    ax.set_xlabel("Time, UTC")
    ax.set_title("{} - {}".format(ts2utc(tss[0]), ts2utc(tss[-1])))
    ax.set_ylabel("Missing DSP reports (max {})".format(maxn))
    ax.text((ts_range) / 2 + tss[0], n.max() * 4 / 5,
            "{:.2f}% missed".format(missed_perc))

    fig.tight_layout()
    pyplot.savefig(args.json_file + "." + args.action.name + suffix + ".png",
                   dpi=480)


def plot_timediff(tss, args=None):
    fig, ax = pyplot.subplots(figsize=(13, 4.8))

    ax.plot(tss[1:], numpy.diff(tss) * 1000, "+")
    ax.xaxis.set_tick_params(which="major", labelsize=4, labelrotation=90)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(200))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(missing_hist_formatter))
    ax.set_xlim(tss[0], tss[-1])
    ax.set_xlabel("Time, UTC")
    ax.set_title("{} - {}".format(ts2utc(tss[0]), ts2utc(tss[-1])))
    ax.set_ylabel("DSP delay, ms")

    fig.tight_layout()
    pyplot.savefig(args.json_file + "." + args.action.name + "timediff.png",
                   dpi=480)


def find_missing_dsp(args, j):
    j = prepare_raw1k(j)
    tss = raw1k_extract_tss(j)
    dsps = raw1k_extract_dsps(j)
    dsps = sorted(dsps, key=lambda i: i[1])

    last_dsp_ts = dsps[0][1]
    missed_dsp = []
    missed_secs = []

    for dsp in dsps[1:]:
        diff = (dsp[1] - last_dsp_ts) // 1000

        if diff > 1:
            print("Missing {}s: {} - {}".format(diff,
                                                ts2utc(last_dsp_ts / 1000),
                                                ts2utc(dsp[1] / 1000)))

            missed_secs.append(diff)
            missed_dsp.extend(range(last_dsp_ts // 1000, dsp[1] // 1000, 1))

        last_dsp_ts = dsp[1]

    plot_missing_hist(tss, missed_dsp, args=args)
    plot_timediff([i[1] / 1000 for i in dsps], args=args)

    _, ax = pyplot.subplots()
    n, bins, _ = ax.hist(missed_secs)
    ax.set_xlabel("Missed, seconds")
    ax.set_ylabel("Count")
    ax.set_title("{} - {}".format(ts2utc(tss[0]), ts2utc(tss[-1])))
    pyplot.savefig(args.json_file + ".secs_hist.png", dpi=480)


def cmp_dsp(args, j):
    cdsp_pattern = re.compile("DSP report: xdr_seq_no<([0-9]*)>, \
xdr_ser_no<([0-9])>, xdr_gmt_time<([0-9]*)>")

    header = j["header"]
    j = prepare_raw1k(j)
    tss = raw1k_extract_tss(j)
    bamlog_dsps = {}
    bamlog_cdsps = {}
    raw1k_dsps = {
            dsp_seqn: (ts, dsp_ts, dsp_seqn)
            for ts, dsp_ts, dsp_seqn in raw1k_extract_dsps(j)
            }

    raw1k_sensor = header["TAG_SENSOR_SER_NO"]["sensor_serial"]

    print("Autodetected sensor as {} ({})"
          .format(raw1k_sensor, header["TAG_SENSOR_SER_NO"]["side"]))

    with open(args.bamlog, "r") as bamlog:
        for line in bamlog:
            line = line.rstrip()
            pattern = FUZION_DSP_PATTERN if args.fuzion else DSP_PATTERN
            match = pattern.search(line)

            if match:
                dsp = match.groups()
                dsp_ints = (int(i) for i in dsp)

                if args.fuzion:
                    version, sensor, seqn, ts_ms, presence = dsp_ints
                    flags = 7
                    ts = ts_ms / 1000
                else:
                    sensor, flags, seqn = dsp_ints
                    parts = line.split(".")
                    dt = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                    microsecond = int(parts[1].split(" ")[0]) * 1000
                    ts = dt.replace(tzinfo=timezone.utc,
                                    microsecond=microsecond).timestamp()

                if sensor == raw1k_sensor:
                    bamlog_dsps[seqn] = (sensor, flags, ts)

            match = cdsp_pattern.search(line)

            if match:
                cdsp = match.groups()
                seqn, sensor, ts_ms = (int(i) for i in cdsp)

                if sensor == raw1k_sensor:
                    bamlog_cdsps[seqn] = (sensor, ts_ms)

    bamlog_dsps_orig = bamlog_dsps

    bamlog_dsps = {
            seqn: dsp for seqn, dsp in bamlog_dsps_orig.items()
            if ((dsp[1] & DABFlags.HAVE_REPORT) != 0 and
                tss[-1] >= dsp[2] >= tss[0])
            }

    print("Parsed {} / {} DSPs from bamlog".format(len(bamlog_dsps),
                                                   len(bamlog_dsps_orig)))

    print("Parsed {} DSPs from raw1k".format(len(raw1k_dsps)))

    if len(bamlog_dsps) < 2:
        print("Not enough DSPs in bamlog after filtering, bailing")

        return

    bamlog_dsps_tss = sorted([ts for _, __, ts in bamlog_dsps.values()])
    bamlog_dsps_missed = [
            dsp for seqn, dsp in bamlog_dsps.items() if seqn not in raw1k_dsps
            ]

    bamlog_seqns = sorted(list(bamlog_dsps.keys()))
    bamlog_jumped_tss = []

    for i, seqn in enumerate(bamlog_seqns[1:], 1):
        last = bamlog_seqns[i - 1]

        if seqn - last != 1:
            seqn_tss = (int(bamlog_dsps[last][2]), int(bamlog_dsps[seqn][2]))
            bamlog_jumped_tss.extend(range(min(seqn_tss), max(seqn_tss)))

            print("Seqno jumped {} -> {} ({:+d})".format(last, seqn,
                                                         seqn - last))

    plot_missing_hist(bamlog_dsps_tss, bamlog_jumped_tss, args=args,
                      suffix=".jumped_seqno")

    for seqn, dsp in bamlog_dsps.items():
        if seqn not in raw1k_dsps:
            print("missed DSP #{} @ {}: {}".format(seqn, ts2utc(dsp[2]), dsp))

    bamlog_missed_tss = [ts for _, __, ts in bamlog_dsps_missed]
    bamlog_missed_flags = [flags for _, flags, __ in bamlog_dsps_missed]

    print("{} DSPs from bamlog are missing in raw1k".format(
        len(bamlog_dsps_missed)))

    bamlog_cdsps = {
            seqn: dsp for seqn, dsp in bamlog_cdsps.items()
            if seqn in bamlog_dsps
            }

    print("Parsed {} custom DSP messages".format(len(bamlog_cdsps)))

    seqns = sorted(bamlog_cdsps.keys())

    if seqns:
        last_ts_ms = bamlog_cdsps[seqns[0]][1]

        for seqn in seqns:
            sensor, ts_ms = bamlog_cdsps[seqn]

            if ts_ms // 1000 == last_ts_ms // 1000:
                print("DSP #{} ts_ms = {}, last_ts_ms = {}"
                      .format(seqn, ts_ms, last_ts_ms))

            last_ts_ms = ts_ms

    plot_missing_hist(bamlog_dsps_tss, bamlog_missed_tss, args=args)
    plot_timediff(bamlog_dsps_tss, args=args)

    fig, ax = pyplot.subplots()
    n, bins, _ = ax.hist(bamlog_missed_flags)
    ax.set_xlabel("DSP flags")
    ax.set_ylabel("Count")
    ax.set_title("{} - {}".format(ts2utc(bamlog_dsps_tss[0]),
                                  ts2utc(bamlog_dsps_tss[-1])))

    fig.tight_layout()
    pyplot.savefig(args.json_file + ".dsp_flags.png", dpi=480)


def main():
    argparser = ArgumentParser(description="Process parsed raw1k files")

    argparser.add_argument("action", type=Action, choices=Action)
    argparser.add_argument("json_file", type=str,
                           help="JSON output from `raw1k.py dump'")

    argparser.add_argument("bamlog", type=str, nargs="?",
                           help="bamlog file")

    argparser.add_argument("--fuzion", action="store_true",
                           help="expect fuzion log format")

    args = argparser.parse_args()
    actions = {
            Action.FIND_MISSING_DSP: find_missing_dsp,
            Action.CMP_DSP: cmp_dsp,
            }

    with open(args.json_file, "r") as f:
        j = json.load(f)

    actions[args.action](args, j)


if __name__ == "__main__":
    main()
