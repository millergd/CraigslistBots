import AWS from "aws-sdk";
AWS.config.update({ region: "us-east-1" });
const dynamodb = new AWS.DynamoDB.DocumentClient();


export function main(event, context, callback) {
  const queryPage = event.pathParameters.page;

  if (queryPage < 0){
    callback(null, {
      statusCode: 500,
      headers: {
        "Access-Control-Allow-Origin" : "*",
        "Access-Control-Allow-Credentials" : true
      },
      body: JSON.stringify({data: 'index out of range'})
    });
    return;
  }

  const qParams = {
    TableName: "random-products",
    Key: {page: -1, id: -1}
  };

  dynamodb.get(qParams).promise().then((data) => {

    console.log(data);





    callback(null, {
      statusCode: 200,
      headers: {
        "Access-Control-Allow-Origin" : "*", // Required for CORS support to work
        "Access-Control-Allow-Credentials" : true // Required for cookies, authorization headers with HTTPS
      },
      body: JSON.stringify({
        outDynamo: data,
        input: event,
      }),
    });
  }).catch((err) => {
    callback(null, {
      statusCode: 500,
      headers: {
        "Access-Control-Allow-Origin" : "*", // Required for CORS support to work
        "Access-Control-Allow-Credentials" : true // Required for cookies, authorization headers with HTTPS
      },
      body: JSON.stringify({ err })
    });
    return;
  });
}