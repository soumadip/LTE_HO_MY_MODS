#$1 = beta value, $2 = expt, $3 = case, $4 = part_no
python gen_config_all_t2.py json-configs/common_config.json $1 $2 $3 $4> tmp/_tmp$1$2$3$4

while read p; do
	echo "Running for $p"
	python common.py $p
done < tmp/_tmp$1$2$3$4

