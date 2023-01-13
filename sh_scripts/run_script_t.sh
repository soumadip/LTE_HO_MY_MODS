#$1 = part of the run seq, $2 = expt, $3 = case
python gen_config_all_t.py json-configs/common_config.json $1 $2 $3 > tmp/_tmp$1$2$3

while read p; do
	echo "Running for $p"
	python common.py $p
done < tmp/_tmp$1$2$3

