if [[ "$1" == "plot" ]]; then
	#plotting code
	python plot.py $2 $3 $4
else
	#for f in `python gen_config.py json-configs/common_config.json`; do
	python gen_config_all.py json-configs/common_config.json $2 > tmp/_tmp
    while read p; do
		echo "Running for $p"
		python common.py $p
	done < tmp/_tmp
fi

