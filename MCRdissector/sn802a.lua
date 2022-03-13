-- to add a new device add its hex value in the packet as a key at the end of the table then make its value the name of the device you want to add
local device_names = {
	[0x0] = "Test Fixture",
	[0x01] = "Pump Device",
	[0x02] = "Pump Controller",
	[0x04] = "Reserved - UV 3BTN REM",
	[0x06] = "Reserved - UV 7BTN REM",
	[0x08] = "Reserved - UV 9BTN REM",
	[0x0A] = "Reserved - Firmware REM Manager",
	[0x11] = "Reserved - Legacy",
	[0x12] = "Reserved - Legacy",
	[0x16] = "Reserved - ASCII Sync BLE",
	[0x18] = "Reserved - ASCII Sync CAN",
	[0x20] = "Voice Controller",
	[0x31] = "Sense and Do Manager",
	[0x32] = "Sense and Do Controller",
	[0x41] = "Foundation Device",
	[0x42] = "Foundation Controller",
	[0x51] = "Sleep Expert Device",
	[0x52] = "Sleep Expert Controller",
	[0x61] = "DualTemp Engine",
	[0x62] = "DualTemp Controller",
	[0x63] = "DualTemp Virtual Engine Right",
	[0x64] = "DualTemp Virtual Engine Left",
	[0x65] = "DualTemp Virtual Controller Right",
	[0x66] = "DualTemp Virtual Controller Left",
	[0x71] = "Proxy Device",
	[0x72] = "Proxy Controller",
	[0x81] = "Bridge Router Device",
	[0x82] = "Bridge Router Controller",
	[0x91] = "Smart Outlet Device",
	[0x92] = "Smart Outlet Controller"
}

-- To append a command to an already existing command class (general, pump, dual temp, ...) then just go to that section in this code and add the appropriate prefix which is detailed in the comment at the beginning of the section
-- To add a new command class go to the bottom of the command list and choose the next available command class prefix then append it to the front of the of the command (command class 9 and command 0x42 -> 0x0942) then look at the command_map table for the next step
-- The reason we did it this way was because we could not find a good consistent pattern in the way that device names corresponded to their command class
local commands = {
	-- this sould only happen if the command id is not valid
	[0x0000] = "Command not recognized",
	-- general command class (1)
	[0x0100] = "Device Query (ACK) Request",
	[0x0101] = "Bind Table Cleared",
	[0x0102] = "Force to Idle State",
	[0x0105] = "Bind Table Modification Request",
	[0x0106] = "Open Bind Window Request",
	[0x0120] = "Get/Set Name Request",
	[0x017D] = "Bind Queue Depth Request",
	[0x0164] = "Radio Channel Change Request",
	[0x0165] = "RSSI (Radio Signal Strength) Request",
	[0x0171] = "Software Revision Request",
	[0x0172] = "Factory Reset Request",
	[0x0180] = "REPLY - Device Query (ACK) Request",
	[0x0181] = "REPLY - Bind Table Cleared",
	[0x0182] = "REPLY - Force to Idle State",
	[0x0185] = "REPLY - Bind Table Modification Request",
	[0x0186] = "REPLY - Open Bind Window Request",
	[0x01A0] = "REPLY - Get/Set Name Request",
	[0x01FD] = "REPLY - Bind Queue Depth Request",
	[0x01E4] = "REPLY - Radio Channel Change Request",
	[0x01E5] = "REPLY - RSSI (Radio Signal Strength) Request",
	[0x01F1] = "REPLY - Software Revision Request",
	[0x01F2] = "REPLY - Factory Reset Request",
	[0x01FE] = "General Unknown Reply (0xFE)",
	-- proxy command class (2)
	[0x0211] = "Modify Device List", 
	[0x0212] = "Proxy Status Request",
	[0x0213] = "Proxy Status Extended Request",
	[0x0291] = "REPLY - Modify Device List",
	[0x0292] = "REPLY - Proxy Status Request",
	[0x0293] = "REPLY - Proxy Status Extended Request",
	-- pump command class (3)
	[0x0303] = "Safe-State Self-Test", 
	[0x0304] = "Firmware",
	[0x0311] = "Set Point Change",
	[0x0312] = "Pump Status",
	[0x0313] = "Memory Value Change",
	[0x0314] = "Memory Value Recall",
	[0x0315] = "Depricated Command",
	[0x0316] = "Adjustment Constant",
	[0x0318] = "Tick Mark Limit",
	[0x0319] = "Reporting System Status",
	[0x031A] = "Pump Current-State",
	[0x031E] = "Timed Deflate Status",
	[0x0322] = "Pump Previous Job Status",
	[0x0324] = "Tank Pressure Test (SN 100)",
	[0x0326] = "In-Home Pump Self-Check",
	[0x0327] = "In-Home Pump State",
	[0x0330] = "Bed Detection Sensitivity",
	[0x0360] = "Leak Test", 
	[0x0361] = "Chamber Presence Change",
	[0x0362] = "LED Override",
	[0x0363] = "ADC",
	[0x0366] = "Get LED State",
	[0x0383] = "REPLY - Safe-State Self-Test",
	[0x0384] = "REPLY - Firmware",
	[0x0391] = "REPLY - Set Point Change",
	[0x0392] = "REPLY - Pump Status",
	[0x0393] = "REPLY - Memory Value Change",
	[0x0394] = "REPLY - Memory Value Recall",
	[0x0396] = "REPLY - Adjustment Constant",
	[0x0398] = "REPLY - Tick Mark Limit",
	[0x0399] = "REPLY - Reporting System Status",
	[0x039A] = "REPLY - Pump Current-State",
	[0x039E] = "REPLY - Timed Deflate Status",
	[0x03A2] = "REPLY - Pump Previous Job Status",
	[0x03A4] = "REPLY - Tank Pressure Test (SN 100)",
	[0x03A6] = "REPLY - In-Home Pump Self-Check",
	[0x03A7] = "REPLY - In-Home Pump State",
	[0x03B0] = "REPLY - Bed Detection Sensitivity",
	[0x03E0] = "REPLY - Leak Test", 
	[0x03E1] = "REPLY - Chamber Presence Change",
	[0x03E2] = "REPLY - LED Override",
	[0x03E3] = "REPLY - ADC",
	[0x03E6] = "REPLY - Get LED State",
	-- dual temp command class (4)
	[0x0403] = "Temperature Self-Test", 
	[0x0411] = "Temperature Set Point",
	[0x0412] = "Temperature Engine Status",
	[0x0413] = "Temperature On/Off Control",
	[0x0414] = "Temperature Engine Read Data",
	[0x0416] = "Temperature Read EEPROM",
	[0x0417] = "Temperature Write EEPROM",
	[0x0418] = "Temperature Functional Test Status",
	[0x0419] = "Temperature Start Functional Test",
	[0x0483] = "REPLY - Temperature Self-Test",
	[0x0491] = "REPLY - Temperature Set Point",
	[0x0492] = "REPLY - Temperature Engine Status",
	[0x0493] = "REPLY - Temperature On/Off Control",
	[0x0494] = "REPLY - Temperature Engine Read Data",
	[0x0496] = "REPLY - Temperature Read EEPROM",
	[0x0497] = "REPLY - Temperature Write EEPROM",
	[0x0498] = "REPLY - Temperature Functional Test Status",
	[0x0499] = "REPLY - Temperature Start Functional Test",
	-- sense and do command class (5)
	[0x0512] = "S&D Status Request",
	[0x0514] = "S&D Configure",
	[0x0515] = "S&D Device Action",
	[0x0516] = "S&D Activity Detected",
	[0x0592] = "REPLY - S&D Status Request",
	[0x0594] = "REPLY - S&D Configure",
	[0x0595] = "REPLY - S&D Device Action",
	[0x0596] = "REPLY - S&D Activity Detected",
	-- foundation command class (6)
	[0x0603] = "Foundation Self-Test", 
	[0x0611] = "Foundation Adjustment Change",
	[0x0612] = "Foundation Adjustment Status Request",
	[0x0613] = "Foundation Outlet Change",
	[0x0614] = "Foundation Outlet Status",
	[0x0615] = "Foundation Activate Preset",
	[0x0616] = "Foundation Store New Preset",
	[0x0617] = "Foundation Reset Preset",
	[0x0618] = "Foundation Read Preset",
	[0x0619] = "Foundation Motion Halt",
	[0x061A] = "Foundation Massage Status",
	[0x0624] = "Foundation Change System Setting",
	[0x0625] = "Foundation System Status",
	[0x0626] = "Foundation Start In-Home Self-Check",
	[0x0627] = "Foundation In-Home Self-Check Status",
	[0x0628] = "Pinch State Request",
	[0x0629] = "Footwarming Change",
	[0x062A] = "Footwarming Status",
	[0x062B] = "Foundation Firmware Image Request",
	[0x062C] = "Footwarming Adv. Diagnostics",
	[0x0683] = "REPLY - Foundation Self-Test",
	[0x0691] = "REPLY - Foundation Adjustment Change",
	[0x0692] = "REPLY - Foundation Adjustment Status",
	[0x0693] = "REPLY - Foundation Outlet Change",
	[0x0694] = "REPLY - Foundation Outlet Status",
	[0x0695] = "REPLY - Foundation Activate Preset",
	[0x0696] = "REPLY - Foundation Store New Preset",
	[0x0697] = "REPLY - Foundation Reset Preset",
	[0x0698] = "REPLY - Foundation Read Preset",
	[0x0699] = "REPLY - Foundation Motion Halt",
	[0x069A] = "REPLY - Foundation Massage Status",
	[0x06A4] = "REPLY - Foundation Change System Setting",
	[0x06A5] = "REPLY - Foundation System Status",
	[0x06A6] = "REPLY - Foundation Start In-Home Self-Check",
	[0x06A7] = "REPLY - Foundation In-Home Self-Check Status",
	[0x06A8] = "REPLY - Pinch State Request",
	[0x06A9] = "REPLY - Footwarming Change",
	[0x06AA] = "REPLY - Footwarming Status",
	[0x06AB] = "REPLY - Foundation Firmware Image",
	[0x06AC] = "REPLY - Footwarming Adv. Diagnostics",
	-- sleep expert command class (7)
	[0x071B] = "Sleep Expert Write Short Key Value",
	[0x071C] = "Sleep Expert Read Short Key Value",
	[0x071D] = "Sleep Expert Long Key Value",
	[0x079B] = "REPLY - Sleep Expert Write Short Key Value",
	[0x079C] = "REPLY - Sleep Expert Read Short Key Value",
	[0x079D] = "REPLY - Sleep Expert Long Key Value",
	-- smart outlet command class (8)
	[0x0812] = "Smart Outlet Status Request",
	[0x0813] = "Smart Outlet Change Request",
	[0x0814] = "Smart Outlet Add/Remove",
	[0x0815] = "Smart Outlet Get/Set Name",
	[0x0816] = "Smart Outlet Output Level Change",
	[0x0817] = "Smart Outlet Output Level Status",
	[0x0818] = "Smart Outlet Firmware Version Request",
	[0x0892] = "REPLY - Smart Outlet Status",
	[0x0893] = "REPLY - Smart Outlet Change",
	[0x0894] = "REPLY - Smart Outlet Add/Remove",
	[0x0895] = "REPLY - Smart Outlet Get/Set Name",
	[0x0896] = "REPLY - Smart Outlet Output Level Change",
	[0x0897] = "REPLY - Smart Outlet Output Level Status",
	[0x0898] = "REPLY - Smart Outlet Firmware Version"
}

-- maps device to command class
-- To add a new command class map, add the command class as a key to this table then make its value a table of device names that are allowed to use the command class
local command_map = {
	[0x01] = device_names,
	[0x02] = { device_names[0x71], device_names[0x72] },
	[0x03] = { device_names[0x01], device_names[0x02] },
	[0x04] = { device_names[0x61], device_names[0x62], device_names[0x63], device_names[0x64], device_names[0x65], device_names[0x66] },
	[0x05] = { device_names[0x31], device_names[0x32] },
	[0x06] = { device_names[0x41], device_names[0x42] },
	[0x07] = { device_names[0x51], device_names[0x52] },
	[0x08] = { device_names[0x91], device_names[0x92] }
}

-- name protocol
ieee802154_sn_proto = Proto("sn", "IEEE 802.15.4 for Sleep Number communications")

--fields showing the raw hex packet
local srcNodeHex = ProtoField.uint8("sn.source_node.hex", "Source Node", base.HEX)
local srcIDHex = ProtoField.uint16("sn.source_node_id.hex", "Source Node ID", base.HEX)
local desIDHex = ProtoField.uint16("sn.destination_node_id.hex", "Destination Node ID", base.HEX)
local nodeMatchHex = ProtoField.uint8("sn.matching_node.hex", "Original Node Class", base.HEX)
local idMatchHex = ProtoField.uint16("sn.matching_id.hex", "Original Node ID", base.HEX)
local cmdIDHex = ProtoField.uint8("sn.command.hex", "Command ID", base.HEX)
local subCmdWithPayload = ProtoField.uint8("sn.subcommand.hex", "Subcommand ID | Payload Length", base.HEX)

-- fields showing the interpretation of the packet
local srcNode = ProtoField.string("sn.source_node", "Source Node", base.ASCII)
local srcID = ProtoField.string("sn.source_node_id", "Source Node ID", base.ASCII)
local desID = ProtoField.string("sn.destination_node_id", "Destination Node ID", base.ASCII)
local nodeMatch = ProtoField.string("sn.node_class", "Original Node Class", base.ASCII)
local idMatch = ProtoField.string("sn.node_id", "Original Node ID", base.ASCII)
local cmdID = ProtoField.string("sn.command_id", "Command ID", base.ASCII) 
local subCmdId = ProtoField.uint8("sn.subcommand", "Subcommand ID", base.HEX)
local payloadLength = ProtoField.uint8("sn.payloadlength", "Payload Length", base.DEC)
local payload = ProtoField.string("sn.payload", "Payload", base.ASCII)
local checksum = ProtoField.uint16("sn.checksum", "Checksum", base.HEX)
local packetLength = ProtoField.uint16("sn.packet_length", "MCR Packet Length", base.DEC)

-- add categories to the protocol
ieee802154_sn_proto.fields = { srcNode, srcID, desID, nodeMatch, idMatch, cmdID, subCmdId, payloadLength, payload, checksum, packetLength,
							   srcNodeHex, srcIDHex, desIDHex, nodeMatchHex, idMatchHex, cmdIDHex, subCmdWithPayload}

-- returns correct key for a command
local function getCommand( command_map, pktSrcNode, pktCmdID )

	local key = 0x0000

	for cmd_class, cmd_class_members in pairs(command_map) do
		for _, cmd_class_member in pairs(cmd_class_members) do

			key = bit32.bor(bit32.lshift(cmd_class, 8), pktCmdID)

			if cmd_class_member == device_names[pktSrcNode] and  commands[key] ~= nil then
				return key
			end

			key = 0x0000

		end
	end

	return key

end

-- setup actual dissector
function ieee802154_sn_proto.dissector( tvbuffer, pinfo, tree )

	--packet details
	local pktSrcNode = tvbuffer(2, 1):uint()
	local pktPayloadLength = bit32.band(tvbuffer(11, 1):uint(), 0x0f)
	local pktPayload = ""

	--grab the correct command
	local key = getCommand(command_map, pktSrcNode, tvbuffer(10, 1):uint())
	
	--populate column data
	pinfo.cols.protocol = ieee802154_sn_proto.name
	pinfo.cols.info = device_names[tvbuffer(2,1):uint()] .. " - " .. commands[key]
	
	--make the subtree
	local subtree = tree:add(ieee802154_sn_proto, tvbuffer(), "IEEE 802.15.4 for Sleep Number Communications")
	local hextree = tree:add(ieee802154_sn_proto, tvbuffer(), "HEX")
	
	--add fields to the detailed subtree
	subtree:add(srcNode, tvbuffer(2,1), string.format("%s (0x%02x)", device_names[pktSrcNode], pktSrcNode))
	subtree:add(srcID, tvbuffer(3,2), string.format("%02x:%02x", tvbuffer(3, 1):uint(), tvbuffer(4, 1):uint()))
	subtree:add(desID, tvbuffer(5,2), string.format("%02x:%02x", tvbuffer(5, 1):uint(), tvbuffer(6, 1):uint()))
	subtree:add(nodeMatch, tvbuffer(7,1), (pktSrcNode == tvbuffer(7, 1):uint()) and "MATCH" or "NON-MATCH")
	subtree:add(idMatch, tvbuffer(8,2), (tvbuffer(3, 2):uint() == tvbuffer(8, 2):uint()) and "MATCH" or "NON-MATCH")
	subtree:add(cmdID, tvbuffer(10,1), string.format("%s (0x%02x)", commands[key], bit32.band(key, 0x0ff))) -- if key is nil then command not recognized
	subtree:add(subCmdId, tvbuffer(11,1), bit32.rshift(tvbuffer(11, 1):uint(), 4))
	subtree:add(payloadLength, tvbuffer(11,1), pktPayloadLength)

	--add the ability to search by hex value
	hextree:add(srcNodeHex, tvbuffer(2,1))
	hextree:add(srcIDHex, tvbuffer(3,2))
	hextree:add(desIDHex, tvbuffer(5,2))
	hextree:add(nodeMatchHex, tvbuffer(7,1))
	hextree:add(idMatchHex, tvbuffer(8,2))
	hextree:add(cmdIDHex, tvbuffer(10,1))
	hextree:add(subCmdWithPayload, tvbuffer(11,1))

	--format the payload bytes
	if pktPayloadLength > 0 then
		--
		for i=0, pktPayloadLength - 1 do
			pktPayload = string.format("%s%02x ", pktPayload, tvbuffer(12+i, 1):uint())
		end

		subtree:add(payload, tvbuffer(12, pktPayloadLength), pktPayload)

	end
	--add the checksum to each tree
	subtree:add(checksum, tvbuffer(12 + pktPayloadLength, 2))
	hextree:add(checksum, tvbuffer(12 + pktPayloadLength, 2))

	--append the packet length to the description subtree
	subtree:add(packetLength, pktPayloadLength + 10)
end

-- register dissector
DissectorTable.get("ethertype"):add(0x809a, ieee802154_sn_proto)