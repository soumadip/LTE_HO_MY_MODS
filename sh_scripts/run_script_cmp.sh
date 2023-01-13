#$1 = part of the run seq
python gen_config_all_cmp.py json-configs/common_config.json $1 > tmp/_tmp$1cmp

while read p; do
	echo "Running for $p"
	python common.py $p
done < tmp/_tmp$1cmp

