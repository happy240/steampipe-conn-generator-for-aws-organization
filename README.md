# Steampipe connection configuration file generator for AWS accounts accross organization

[Steampipe](https://github.com/turbot/steampipe) is an excellent utility which users can use SQL to instantly query your cloud services (AWS, Azure, GCP and more).

When use steampipe for AWS organization accounts at scale, [build connection configuration file](https://steampipe.io/docs/managing/connections) can be a complex and time consuming task. This python script generate steampipe connection file(.spc) for accounts and OUs in specified AWS organization.

## Prerequisites:
Genspc4awsorg script need to run under an account which has AWS organization APIs permissions, please make sure correct AWS credential in envs(using [aws-vault](https://github.com/99designs/aws-vault) to store and switch AWS credentials is recommend), and base credential profile which can AssumeRole to all accounts accross organization has been configured.

### Some template for ~/.aws/config:
```
[profile common]
region = cn-north-1

[profile <PROFILE NAME>]
include_profile = common
role_arn = arn:aws-cn:iam::<ACCOUNTID>:role/AdminRoleForFederatedUser
```

### Some template for ~/.aws/credentials:
```
[<PROFILE NAME>]
credential_process = aws-vault exec -j <PROFILE NAME> --region=cn-north-1
```

### Permission requirement
genspc4awsorg need to call AWS organization APIs through organization management account or an AWS service delegation administrator account: 
https://docs.amazonaws.cn/en_us/organizations/latest/userguide/orgs_integrate_services_list.html
https://docs.aws.amazon.com/organizations/latest/userguide/orgs_integrate_services_list.html

Delegated administrator account and service infomation can be viewed through following command：
```
aws organizations list-delegated-administrators
aws organizations list-delegated-services-for-account --account-id <account_id>
```

## Install
```
pip install genspc4awsorg
```

## Upgrade
```
pip install --upgrade genspc4awsorg
```

## How genspc4awsorg works
This script will travers accounts and OUs accross AWS organization and generate an .spc file in ~/.steampipe/config/.
There will be a connection for every account with name rule '<PREFIX_ACCOUNT ID>', and a aggregator connection with name rule '<PREFIX_OU NAME>'.
genspc4awsorg will create profiles in ~/.aws/config for every accounts by default, which can be used with awscli and other tools, this action can be ignored with -nc switch.

## Usage
```
usage: genspc4awsorg [-h] [-sp SOURCEPROFILE] [-mfa MFASERIAL] [-ir] [-r ROLENAME] [-nc] [-si SOURCE_IDENTITY]
                     [-st SESSION_TAGS] [-tst TRANSITIVE_SESSION_TAGS] [-ttl CACHE_TTL] [-p PROFILE]
                     orgprefix

Generate steampipe connection file(.spc) for accounts and OUs in specified AWS organization.Before run this script, please   
make sure correct AWS credential in envs(using aws-vault is recommend), and base credential profile which can AssumeRole to  
accounts accross organization has been configured.

positional arguments:
  orgprefix             Prefix for AWS organization, used in steampipe connection names.

optional arguments:
  -h, --help            show this help message and exit
  -sp SOURCEPROFILE, --sourceprofile SOURCEPROFILE
                        AWS credential profile(in ~/.aws/credentials) which can AssumeRole to accounts accross
                        organization.if not provided, default to same value of $orgprefix.Ignored when use "--useec2role"    
                        option.
  -mfa MFASERIAL, --mfaserial MFASERIAL
                        Mfa serial arn used to access target account.
  -ir, --useec2role     Use EC2 Instance Role credential instead of source profile.
  -r ROLENAME, --rolename ROLENAME
                        Role name used to access target account. Default to "OrganizationAccountAccessRole"
  -nc, --ignoreconfigprofile
                        Create steampipe connection config only, NO ~/.aws/config profiles.
  -si SOURCE_IDENTITY, --source_identity SOURCE_IDENTITY
                        "source_identity" in ~/.aws/config profile.
  -st SESSION_TAGS, --session_tags SESSION_TAGS
                        "session_tags" in ~/.aws/config profile.
  -tst TRANSITIVE_SESSION_TAGS, --transitive_session_tags TRANSITIVE_SESSION_TAGS
                        "transit_session_tags" in ~/.aws/config profile.
  -ttl CACHE_TTL, --cache_ttl CACHE_TTL
                        Cache TTL in seconds. Default to 300.
  -p PROFILE, --profile PROFILE
                        Base profile used to get organization info.
```