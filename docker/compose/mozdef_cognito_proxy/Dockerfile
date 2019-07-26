FROM openresty/openresty:centos
ADD docker/compose/mozdef_cognito_proxy/files/default.conf /etc/nginx/conf.d/default.conf
ADD docker/compose/mozdef_cognito_proxy/files/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
RUN touch /etc/nginx/htpasswd
RUN /usr/local/openresty/luajit/bin/luarocks install lua-resty-jwt
RUN yum install -y httpd-tools && yum clean all && rm -rf /var/cache/yum
CMD bash -c "/usr/bin/htpasswd  -bc /etc/nginx/htpasswd mozdef $basic_auth_secret 2> /dev/null; /usr/bin/openresty -g 'daemon off;'"
