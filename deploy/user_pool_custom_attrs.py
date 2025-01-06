import argparse

import boto3

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add patient's custom attributes to a userpool schema"
    )
    parser.add_argument(
        "userPoolId",
        type=str,
        help="user pool id to which we want to add custom attributes",
    )

    args = parser.parse_args()
    client = boto3.client("cognito-idp")
    response = client.add_custom_attributes(
        UserPoolId=args.userPoolId,
        CustomAttributes=[
            {
                "Name": "practiceid",
                "AttributeDataType": "String",
                "DeveloperOnlyAttribute": False,
                "Mutable": True,
                "Required": False,
            },
            {
                "Name": "patientid",
                "AttributeDataType": "String",
                "DeveloperOnlyAttribute": False,
                "Mutable": True,
                "Required": False,
            },
            {
                "Name": "departmentid",
                "AttributeDataType": "String",
                "DeveloperOnlyAttribute": False,
                "Mutable": True,
                "Required": False,
            },
            {
                "Name": "termsAndCondTime",
                "AttributeDataType": "DateTime",
                "DeveloperOnlyAttribute": False,
                "Mutable": True,
                "Required": False,
            },
            {
                "Name": "edd",
                "AttributeDataType": "String",
                "DeveloperOnlyAttribute": False,
                "Mutable": True,
                "Required": False,
            },
            {
                "Name": "enterpriseid",
                "AttributeDataType": "String",
                "DeveloperOnlyAttribute": False,
                "Mutable": True,
                "Required": False,
            },
        ],
    )
