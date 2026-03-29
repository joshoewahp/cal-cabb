#!/usr/bin/sh

load_bigcat_data () {

    proj_dir=$1
    data_dir=$2
    noflag=$3
    pcode=$4
    shiftra=$5
    shiftdec=$6

    mkdir -p "$proj_dir"/miriad

    # Move into data directory to avoid absolute path names which overflow the atlod input parameter
    cd "$data_dir" || exit

    # Copy to reduction directory
    cp -r *uv.fits "$proj_dir"/miriad/.

    cd "$proj_dir"/miriad || exit

    echo "converting..."
    ext=".uv.fits"
    # Convert all UVfits files to miriad UV
    for fitsfile in *uv.fits; do
	echo "converting $fitsfile"

	fname="${fitsfile%$ext}"
	fits in=$fitsfile  out=$fname.uv  op=uvin

	# # Optionally shift phasecenter. This is to be used when you have offset the phasecenter
	# # during an observation (e.g. by -120 arcsec in declination) to avoid DC correlator
	# # errors. Correction would be to shift by +120 arcsec here.
	# if [[ $shiftra -ne 0 ]] || [[ $shiftdec -ne 0 ]]; then
	#     echo "Shifting phasecentre by RA=$shiftra Dec=$shiftdec"
	#     uvedit vis="$pcode".uv ra="$shiftra" dec="$shiftdec" out="$pcode".fix.uv
	#     rm -r "$pcode".uv
	#     mv "$pcode".fix.uv "$pcode".uv
	# fi

	uvsplit vis=$fname.uv
	rm -r $fitsfile $fname.uv

	# rename 2101 2100 *
    done

    # for uvfile in *2150; do
    # 	echo $uvfile
    # 	# uvflag vis=$uvfile select="ant(3)" flagval=flag
	# uvflag vis=$uvfile select="antennae(1)" flagval=flag
	# uvflag vis=$uvfile select="antennae(5)" flagval=flag
	# uvflag vis=$uvfile select="ant(6)" flagval=flag
	# uvflag vis=$uvfile line=channel,160,1,1,1 flagval=flag
	# uvflag vis=$uvfile line=channel,150,370,1,1 flagval=flag
	# uvflag vis=$uvfile line=channel,130,640,1,1 flagval=flag
	# uvflag vis=$uvfile line=channel,27,1000,1,1 flagval=flag
	# uvflag vis=$uvfile line=channel,70,1480,1,1 flagval=flag
    # done

}

load_data() {

    proj_dir=$1
    data_dir=$2
    noflag=$3
    pcode=$4
    shiftra=$5
    shiftdec=$6

    mkdir -p "$proj_dir"/miriad

    if $noflag; then
	atlod_options=noauto,xycorr,notsys
    else
	atlod_options=birdie,rfiflag,noauto,xycorr,notsys
    fi

    # Move into data directory to avoid absolute path names which overflow the atlod input parameter
    cd "$data_dir" || exit

    # Identify RPFITS files from top-level data directory so that backup scans (e.g. 1934)
    # can sit in subdirectories of the data directory without being auto-imported
    infiles=$(find -L ./* -maxdepth 1 -type f | grep "$pcode" | tr '\n' ',' | head -c -1)

    atlod in="$infiles" out="$pcode".uv ifsel="$ifsel" options="$atlod_options"

    mv "$pcode".uv "$proj_dir"/miriad/.
    cd "$proj_dir"/miriad || exit

    # Optionally shift phasecenter. This is to be used when you have offset the phasecenter
    # during an observation (e.g. by -120 arcsec in declination) to avoid DC correlator
    # errors. Correction would be to shift by +120 arcsec here.
    if [[ $shiftra -ne 0 ]] || [[ $shiftdec -ne 0 ]]; then
	echo "Shifting phasecentre by RA=$shiftra Dec=$shiftdec"
	uvedit vis="$pcode".uv ra="$shiftra" dec="$shiftdec" out="$pcode".fix.uv
	rm -r "$pcode".uv
	mv "$pcode".fix.uv "$pcode".uv
    fi

    uvflag vis="$pcode".uv line=channel,160,1,1,1 flagval=flag
    uvflag vis="$pcode".uv line=channel,150,370,1,1 flagval=flag
    uvflag vis="$pcode".uv line=channel,130,640,1,1 flagval=flag
    uvflag vis="$pcode".uv line=channel,27,1000,1,1 flagval=flag
    uvflag vis="$pcode".uv line=channel,70,1480,1,1 flagval=flag

    uvsplit vis="$pcode".uv

}

uvtofits() {

    uv=$1
    fits=$2

    fits in="$uv" out="$fits" op=uvout

}

manflag() {

    vis=$1
    x=$2
    y=$3
    flagoptions=$4

    blflag vis="$vis" device=/xs stokes=xx,yy,xy,yx axis="$x","$y" options="$flagoptions"

}

autoflag() {

    vis=$1

    pgflag vis="$vis" command="<b" device=/xs stokes=xx,yy,xy,yx options=nodisp
    pgflag vis="$vis" command="<b" device=/xs stokes=xx,yy,yx,xy options=nodisp

}

flag_timerange() {

    vis=$1
    start_time=$2
    end_time=$3

    uvflag vis="$vis" select="time($start_time,$end_time)" flagval=flag

}

cal_bandpass() {

    vis=$1
    interpolate=$2

    if $interpolate; then
	mfcal vis="$vis" interval="$mfinterval","$mfinterval","$bpinterval" options=interpolate refant="$refant"
    else
	mfcal vis="$vis" interval="$mfinterval","$mfinterval","$bpinterval" refant="$refant"
    fi

}

cal_delays() {

    vis=$1

    mfcal vis="$vis" interval=300 refant="$refant" options=delay
}

extend_interval() {

    vis=$1

    puthd in=$vis/interval value=10.0 type=double
}

cal_gains() {

    vis=$1
    options=$2

    gpcal vis="$vis" interval="$gpinterval" options="$options" minants=3 nfbin="$nfbin" spec="$spec" refant="$refant"
}

copy_cal() {

    pcal=$1
    scal=$2

    gpcopy vis="$pcal" out="$scal"
}

copy_1934() {

    pcal=$1
    scal=$2

    gpcopy vis="$pcal" out="$scal" options=nocal,nopass

}


bootstrap() {

    scal=$1
    pcal=$2

    gpboot vis="$scal" cal="$pcal"
}

average_gains() {

    cal=$1

    gpaver vis="$cal" interval=2

}

apply_gains() {

    cal=$1

    uvaver vis="$cal" out="$cal".cal

}
