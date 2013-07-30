keystone_ldapauth
=================

keystone의 기본 ldap backend driver는 

 - ldap server에 read / write 권한을 가지고 OpenStack system user(nova, glance, ....) 뿐만 아니라,
   system tenant(service)까지 모두 ldap에서 관리하도록 되어있다.

 - 인증을 위해 1. 사용자 정보를 가져오고 2. hash 된 암호를 비교한다.

하지만 회사에서 사용하는 ldap server를 사용하는 경우라면 

  - 생성 및 수정권한이 없고 사용자 개별 인증을 위해 사용하는 경우가 많다. 즉, read only 계정도 없을 수 있다.
  - ldap은 정보를 가져오기 위해서 bind만 하는데도 개발 인증이 인증이 필요한 경우도 있다.

이런 상황에서는 기본으로 제공되는 ldap backend를 사용할 수 없고,
인증은 ldap으로, 사용자 생성, tenant membership은 기존 SQL Driver에서 관리하는 방법이 좋을 것 같다.

Process
=======
- 인증을 위해 User 정보를 가져올 때..
- SQL에서 인증
- 실패하면 ldap 인증 확인하고
- 인증에 성공하면 그 정보로 사용자를 SQL에 생성
    
Patch Needed
============
keystone.token.controller.Auth에서 get_user_by_name을 호출하는 부분에서
password도 같이 전달해 준다.

그래야 사용자를 SQL에서 lookup해서 없을 경우 그 password를 이용해서 dap에서 인증하고, 여기서
인증에 성공하면 입력한 정보와 ldap에서 받은 정보로 새로운 사용자를 SQL에 추가할 수 있다.

Limits
======
- 인증은 LDAP을 이용하기 때문에 SQL에 암호를 수정해도 변화없음

Requirements
============
- py-ldap

Configuration
=============

in keystone.conf:

    [identity]
    driver = keystone_ldapauth.ldap_auth.Identity
    
    [ldap_auth]
    url = ldap://localhost
    ldap_postfix = prefix
    email_prefix = @your_domain.com
    default_project = default
    member_role = Member
