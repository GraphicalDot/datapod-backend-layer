
download_code () {
    local OUTPUT=$1
    aws lambda get-function --function-name $OUTPUT --query 'Code.Location' | xargs wget -O ./lambda_functions/$OUTPUT.zip  
}

mkdir -p lambda_functions

for run in $(aws lambda list-functions | cut -f 6 | xargs);
do
	download_code "$run" &
done

echo "Completed Downloading all the Lamdba Functions!"