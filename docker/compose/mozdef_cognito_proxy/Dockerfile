FROM openresty/openresty:centos
ADD docker/compose/mozdef_cognito_proxy/files/htpasswd.example /etc/nginx/htpasswd
ADD docker/compose/mozdef_cognito_proxy/files/default.conf /etc/nginx/conf.d/default.conf
ADD docker/compose/mozdef_cognito_proxy/files/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
RUN /usr/local/openresty/luajit/bin/luarocks install lua-resty-jwt
