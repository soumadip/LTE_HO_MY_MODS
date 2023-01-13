#$1 = beta value, $2 = expt, $3 = case, $4 = part no
python gen_config_amst.py json-configs/amst_common_config.json $1 $2 $3 $4 > tmp/_tmp$1$2$3$4

while read p; do
	echo "Running for $p"
	python common.py $p
done < tmp/_tmp$1$2$3$4

