# MozDef Bot

## Available Options

We currently support the following options. Our default is to use slack, but if you would like to use some other protocol besides slack, there is a requirements file in each of the sub directories that you will need to install.

### Slack

#### SlackClient
We currently use https://github.com/slackapi/python-slackclient as our library to interact with Slack.

##### Installation

By default, our requirements.txt file includes the slackbot dependency, so no additional steps are needed for installation


### IRC

#### KitnIRC - A Python IRC Bot Framework

KitnIRC is an IRC framework that attempts to handle most of the
monotony of writing IRC bots without sacrificing flexibility.

##### Installation

    pip install -r bot/irc/requirements.txt

##### Usage

See the `skeleton` directory in the root level for a starting code skeleton
you can copy into a new project's directory and build off of, and
[Getting Started](https://github.com/ayust/kitnirc/wiki/Getting-Started)
for introductory documentation.

##### License

KitnIRC is licensed under the MIT License (see `LICENSE` for details).

##### Other Resources

Useful reference documents for those working with the IRC protocol as a client:

 * [RFC 2812](https://tools.ietf.org/html/rfc2812)
 * [ISUPPORT draft](https://tools.ietf.org/html/draft-brocklesby-irc-isupport-03)
 * [List of numeric replies](https://www.alien.net.au/irc/irc2numerics.html)
