import boto3
import configparser
import os
import argparse
import re

def GenConfigProfile4Account(accountid):
    accountsection='profile '+orgprefix+'_'+accountid[-4:]
    if accountsection not in cf.sections():
        cf.add_section(accountsection)
    cf.set(accountsection,'source_profile',sourceprofile)
    if mfa_serial!='':
        cf.set(accountsection,'mfa_serial',mfa_serial)
    cf.set(accountsection,'role_arn','arn:'+session.get_partition_for_region(session.region_name)+':iam::'+accountid+':role/'+rolename)

def GenCredentialsProfile4Account(accountid):
    sectionname=orgprefix+'_'+accountid
    if sectionname not in cf.sections():
        cf.add_section(sectionname)
    cf.set(sectionname,'source_profile',orgprefix+'_base')
    cf.set(sectionname,'role_arn','arn:'+session.get_partition_for_region(session.region_name)+':iam::'+accountid+':role/'+rolename)

def GenSteampipeConnection4Account(accountid):
    sectionname=orgprefix+'_'+accountid
    if sectionname not in cf.sections():
        cf.add_section(sectionname)
    cf.set(sectionname,'plugin','"aws"')
    cf.set(sectionname,'profile','"'+orgprefix+'_'+accountid+'"')
    cf.set(sectionname,'regions','["'+'","'.join(session.get_available_regions('s3',session.get_partition_for_region(session.region_name)))+'"]')

def GenSteampipeConnection4OU(ouid,isroot):
    #获取OU Name
    if not isroot:
        response = client.describe_organizational_unit(
            OrganizationalUnitId=ouid
        )
        ouname=response['OrganizationalUnit']['Name']
        if ouname not in oudict:
            oudict[ouname]=[]
            oudict[ouname+'_T']=[]
    else:
        ouname=ouid
        if ouname not in oudict:
            oudict[ouname]=[]
    
    #记录OU下Account list
    ouaccountlist = []
    response = client.list_children(
        ParentId=ouid,
        ChildType='ACCOUNT'
    )
    if 'NextToken' in response:
        while 'NextToken' in response:
            ouaccountlist.extend(response['Children'])
            response = client.list_children(
                ParentId=ouid,
                ChildType='ACCOUNT',
                NextToken = response['NextToken']
            )
    ouaccountlist.extend(response['Children'])

    for accountel in response['Children']:
        oudict[ouname].append(accountel['Id'])
        if not isroot:
            oudict[ouname+'_T'].append(accountel['Id'])
        for pou in parentlist:
            oudict[pou].append(accountel['Id'])

    #遍历OU Tree
    suboulist = []
    response = client.list_children(
        ParentId=ouid,
        ChildType='ORGANIZATIONAL_UNIT',
    )
    if 'NextToken' in response:
        while 'NextToken' in response:
            suboulist.append(response['Children'])
            response = client.list_children(
                ParentId=ouid,
                ChildType='ORGANIZATIONAL_UNIT',
                NextToken = response['NextToken']
            )
    suboulist.append(response['Children'])

    if len(response['Children'])>0 and not isroot:
        parentlist.append(ouname+'_T')
    for ouel in response['Children']:
        GenSteampipeConnection4OU(ouel['Id'],False)
    if len(response['Children'])>0 and not isroot:
        parentlist.pop()

def main():
    global orgprefix
    global sourceprofile
    global mfa_serial
    global rolename
    global cf
    global session
    global client
    global oudict
    global parentlist
    global createawsconfigprofile
    global steampipeinipath

    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description='Generate steampipe connection file(.spc) for accounts and OUs in specified AWS organization.'+ \
                                    'Before run this script, please make sure correct AWS credential in envs(using aws-vault is recommend), '+ \
                                    'and base credential profile which can AssumeRole to accounts accross organization has been configured.')
    parser.add_argument('orgprefix', help='Prefix for AWS organization, used in steampipe connection names.')
    parser.add_argument('-sp','--sourceprofile', help='AWS credential profile(in ~/.aws/credentials) which can AssumeRole to accounts accross organization.'+ \
                        'if not provided, default to same value of $orgprefix')
    parser.add_argument('-mfa','--mfaserial', help='Mfa serial arn used to access target account.')
    parser.add_argument('-r','--rolename', help='Role name used to access target account. Default to "OrganizationAccountAccessRole"')
    parser.add_argument('-nc','--ignoreconfigprofile', dest='createawsconfigprofile', action='store_false', help='Create steampipe connection config only, NO ~/.aws/config profiles.')
    parser.set_defaults(createawsconfigprofile=True)
    args = parser.parse_args()

    # Parse args
    orgprefix=args.orgprefix

    if args.sourceprofile:
        sourceprofile=args.sourceprofile
    else:
        sourceprofile=orgprefix

    if args.mfaserial:
        mfa_serial=args.mfaserial
    else:
        mfa_serial=''

    if args.rolename:
        rolename=args.rolename
    else:
        rolename='OrganizationAccountAccessRole'

    createawsconfigprofile=args.createawsconfigprofile
    cf = configparser.ConfigParser()

    #~/.steampipe/config/<connection file>
    #读取steampipe connection配置文件
    steampipeinipath = os.path.join(os.path.expanduser('~'), '.steampipe/config/aws-'+orgprefix+'.ini')
    steampipespcpath = os.path.join(os.path.expanduser('~'), '.steampipe/config/aws-'+orgprefix+'.spc')

    # Init boto3 client
    session=boto3.session.Session()
    client = boto3.client('organizations')

    #遍历Organizatoin accounts
    accountlist=[]
    response = client.list_accounts(
    )
    if 'NextToken' in response:
        while 'NextToken' in response:
            accountlist.extend(response['Accounts'])
            response = client.list_accounts(
                NextToken = response['NextToken']
            )
    accountlist.extend(response['Accounts'])
    #~/.aws/config profiles
    if createawsconfigprofile:
        #读取aws config配置文件
        awsconfigpath = os.path.join(os.path.expanduser('~'), '.aws/config')
        cf.read(awsconfigpath)

        #生成aws config配置文件条目
        for accountel in accountlist:
            GenConfigProfile4Account(accountel['Id'])
        with open(awsconfigpath, 'w') as configfile:
            cf.write(configfile)
        cf = configparser.ConfigParser()

    #~/.aws/credentials
    #读取aws credentials配置文件
    awscredpath = os.path.join(os.path.expanduser('~'), '.aws/credentials')
    cf.read(awscredpath)
    if orgprefix+'_base' not in cf.sections():
        cf.add_section(orgprefix+'_base')
    cf.set(orgprefix+'_base','credential_process','aws-vault exec -j '+sourceprofile+' --region='+session.region_name)

    #生成aws credentials配置文件条目
    for accountel in accountlist:
        GenCredentialsProfile4Account(accountel['Id'])
    with open(awscredpath, 'w') as configfile:
        cf.write(configfile)
    cf = configparser.ConfigParser()

    #为每个account生成steampipe connection config配置文件条目
    cf.read(steampipeinipath)
    for accountel in accountlist:
        GenSteampipeConnection4Account(accountel['Id'])

    #为每个OU生成steampipe connection config配置文件条目
    #构建每个OU下的Account List, 不带"_T"为仅包含当前OU的Accounts, 带"_T"结尾为包含子OU的Accounts
    oudict={}
    parentlist=[]

    #遍历Organizatoin accounts
    response = client.list_roots(
    )
    rootlist = []
    if 'NextToken' in response:
        while 'NextToken' in response:
            rootlist.extend(response['Roots'])
            response = client.list_roots(
                NextToken = response['NextToken']
            )
    rootlist.extend(response['Roots'])
    for rootel in rootlist:
        GenSteampipeConnection4OU(rootel['Id'],True)

    #为整个Organization生成steampipe connection config配置文件条目
    for ouname in oudict:
        if len(oudict[ouname])>0:
            #处理ouname中不符合connection配置要求的字符
            sectionname=re.sub(r'^r\-','',ouname)
            sectionname=re.sub(r'[ @\-]','_',sectionname)

            sectionname=orgprefix+'_'+sectionname
            if sectionname not in cf.sections():
                cf.add_section(sectionname)
            cf.set(sectionname,'type','"aggregator"')
            cf.set(sectionname,'plugin','"aws"')
            cf.set(sectionname,'connections','["'+orgprefix+'_'+('","'+orgprefix+'_').join(oudict[ouname])+'"]')

    sectionname=orgprefix+'_all'
    if sectionname not in cf.sections():
        cf.add_section(sectionname)
    cf.set(sectionname,'type','"aggregator"')
    cf.set(sectionname,'plugin','"aws"')
    cf.set(sectionname,'connections','["'+orgprefix+'_*"]')

    with open(steampipeinipath, 'w') as configini:
        cf.write(configini)
    cf = configparser.ConfigParser()

    #Convert temp ini file to '.spc' file
    with open(steampipeinipath, 'r+') as configini:
        iniconf = configini.read()
        iniconf = re.sub(r'^([^\[|\n])',r'\t\1',iniconf,flags=re.M)
        iniconf = re.sub(r'^\n','}\n',iniconf,flags=re.M)
        spcconf = re.sub(r'(^\[)([a-zA-Z0-9_\- ]+)(]\n)',r'connection "\2" {\n',iniconf,flags=re.M)
    with open(steampipespcpath, 'w') as configspc:
        configspc.write(spcconf)

if __name__ == "__main__":
    sys.exit(main())