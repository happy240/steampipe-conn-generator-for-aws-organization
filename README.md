Generate steampipe connection file(.spc) for accounts and OUs in specified AWS

organization.Before run this script, please make sure correct AWS credential

in envs(using aws-vault is recommend), and base credential profile which can

AssumeRole to accounts accross organization has been configured.

## Install
```
pip install genspc4awsorg
```

## Usage
```
genspc4awsorg.py \[-h\] \[-sp SOURCEPROFILE\] \[-mfa MFASERIAL\]

                        \[-r ROLENAME\] \[-nc\]

                        orgprefix
```
positional arguments:

  orgprefix             Prefix for AWS organization, used in steampipe

                        connection names.

optional arguments:

  -h, --help            show this help message and exit

  -sp SOURCEPROFILE, --sourceprofile SOURCEPROFILE

                        AWS credential profile(in ~/.aws/credentials) which

                        can AssumeRole to accounts accross organization.if not

                        provided, default to same value of $orgprefix

  -mfa MFASERIAL, --mfaserial MFASERIAL

                        Mfa serial arn used to access target account.

  -r ROLENAME, --rolename ROLENAME

                        Role name used to access target account. Default to

                        "OrganizationAccountAccessRole"

  -nc, --ignoreconfigprofile

                        Create steampipe connection config only, NO

                        ~/.aws/config profiles.