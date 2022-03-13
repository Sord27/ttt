HOME_DIR=/home/jenkins/offline-tester-linux
if [ -z "$1" ]
  then
    echo "No argument for branch is supplied"
    exit
fi
if [ -z "$2" ]
  then
    echo "No argument for test folder is provided"
    exit
  else
    PRESSURE_FOLDER=$HOME_DIR/$2
    if [ -d $PRESSURE_FOLDER ]; then
            rm -rf $PRESSURE_FOLDER
    else
            mkdir $PRESSURE_FOLDER
    fi
    aws s3 sync s3://siq-dev-algo/$2/ $PRESSURE_FOLDER
fi
if [ -z "$3" ]
  then
    echo "No audio folder provided"
  else
    AUDIO_FOLDER=$HOME_DIR/$3/
    if [ -d $AUDIO_FOLDER ]; then
            rm -rf $AUDIO_FOLDER
    else
            mkdir $AUDIO_FOLDER
    fi
    aws s3 sync s3://siq-dev-algo/$3/ $AUDIO_FOLDER
fi
GIT_HOME=$HOME_DIR/gitDir/BAM_Algo/
GIT_BRANCH=$1
ALGO_DIR=$HOME_DIR
pushd $GIT_HOME
git checkout $GIT_BRANCH
git pull origin
popd
pushd $GIT_HOME
make clean
make
popd
DLL_DIR=$GIT_HOME/build/linux-m64
rm $ALGO_DIR/native/*
mv $DLL_DIR/libBAMAnalysisDLL64.so  $ALGO_DIR/native
i1=$1
i2=$2
i3=$3
if [ -z "$3" ]
     then
    java -Xms1200m -Xmx4000m -Djava.library.path=$HOME_DIR/native -classpath ./lib/* com.bam.tools.analysis.AnalysisTester -concatFiles -mode process -threads 30 -disableHRRRDetection -outputPlots -file $PRESSURE_FOLDER
     else
    i4=$4
    i5=$5
    i6=$6
    i7=$7
    i8=$8
    i9=$9
    shift
    i10=$9
    shift
    i11=$9
echo $AUDIO_FOLDER
echo $PRESSURE_FOLDER
java -Xms2200m -Xmx31000m -Xincgc -Xloggc:$HOME_DIR/gc.log -Djava.library.path=$HOME_DIR/native -classpath ./lib/* com.bam.tools.analysis.AudioDataTester -concatFiles -mode process -threads 4 -disableHRRRDetection -outputPlots -rawDataSource $PRESSURE_FOLDER -audioDataSource $AUDIO_FOLDER $i4 $i5 $i6 $i7 $i8 $i9 $i10 $i11
fi
rm -rf $PRESSURE_FOLDER/*.mem
aws s3 sync $PRESSURE_FOLDER s3://siq-dev-algo/$i2/