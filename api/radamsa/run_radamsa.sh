docker build -f radamsa.Dockerfile -t radamsa-fuzzer .

if [[ -z "$1" || -z "$2" || -z "$3" || -z "$4" || -z "$5" ]]; then
    echo -e "\nTo run the script, use:\n\t./run_radamsa.sh <voyeur_user> <voyeur_pass> <arg_method> <arg_payload> <arg_path>\n"
    exit 1
fi
name=$(echo $5 | tr "/?=" "-" | tr -d "{}")

docker run -d --rm \
    --name=fuzzing$name \
    -e NAME=$1 \
    -e PASS=$2 \
    -e INFINITE=1 \
    -v $PWD/../data:/app/data:ro \
    --network=host \
    radamsa-fuzzer $3 $5 $4

