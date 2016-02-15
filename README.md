# Ore

[![Build Status](https://travis-ci.org/SpongePowered/Ore.svg?branch=master)](https://travis-ci.org/SpongePowered/Ore)
[![Slack Status](https://slackin.spongepowered.org/badge.svg)](https://slackin.spongepowered.org)

__Travelers, BEWARE!!__ This is essentially _gamma_-stage software.
While bugfixes and PRs and such are welcome, they will most likely get overwritten as I develop this app further.

There is an instance staged to https://ore-staging.spongepowered.org with docker and magic web scale sauce™.
Don't get too attached to whatever you put there, because it's most likely going to be reset.

Also see [ore-frontend](https://github.com/gratimax/ore-frontend), the frontend for Ore.

## Faq

__Q: Why is this on GitHub?__

Simply put, FOSS(Free and Open Source Software) is the best software.
We dislike the closed nature of BukkitDev, and as part of the goal of moving the Minecraft community forward we
have decided to open-source this project and MIT-license from the start.
Anyone can contribute, make an issue or PR, or read the source freely.

This also allows users to run their own Ore repositories if they wish, and we hope to make that easier by
sticking this project in a Docker container.

__Q: Is this project more like BukkitDev or a package manager?__

Yes.

__Q: Elaborate?__

In its current stages Ore looks more like an open-source version of BukkitDev (BOOYAH open source software!).
We plan to eventually create a package manager that consumes an Ore repository that can install plugins.

__Q: So I should tell my doctor to not go ahead with the operation of surgically attaching me to it?__

We're very excited for the possibilities of this project in causing the machine-human singularity but please remember
that it is a zeta-level feature.

__Q: More FAQ soon?__

Yes.

## Development

Written with Python 3 and Django 1.9. Requires [Node.js](https://nodejs.org/en/)
You should probably use virtualenv.

1.  Create a new virtualenv - my suggestion is to use `virtualenv venv` in the root of the project.
2.  Enter the virtualenv - if you followed my instruction about, use `source venv/bin/activate`.
3.  Install the requirements - `pip install -r requirements/development.txt`
4.  Set up the database - our base development settings expect a database with name `repo`, user `admin` and password `password`.
5.  Install Node.js dependencies - `npm install`
6.  Perform a migration - `python ore/manage.py migrate`
7.  Start the web server - `python ore/manage.py runserver`

Note that we use Postgres, both in production and development. We can and probably will choose to use Postgres-only features, so beware!

## How to run

Builds are automatically published to [the central Docker registry](https://registry.hub.docker.com/u/spongepowered/ore/).

The application environment is determined by which [setting configuration](https://github.com/SpongePowered/Ore/tree/master/ore/settings) is passed
into the `DJANGO_SETTINGS_MODULE` environment variable.

Other environment variables to note:

- `SECRET_KEY`: the secret key of the application, used for cookies and other secret things
- `DB_USER`: the database user
- `DB_PASSWORD`: the database password
- `DB_NAME`: which database to connect to, default 'repo'
- `WEBDB_PORT_5432_TCP_PORT`: the port of the database to connect to, provided by docker if the container is run with `--link <postgres>:webdb`
- `WEBDB_PORT_5432_TCP_ADDR`: the host of the database to connect to, provided by docker if the container is run with `--link <postgres>:webdb`

```bash
$ docker run -dP --name webdb \
    -e POSTGRES_USER=repo -e POSTGRES_PASSWORD=much_secret \
    postgres

$ docker run -dp 80:80 --link webdb:webdb \
    -e DB_USER=repo -e DB_PASSWORD=much_secret -e SECRET_KEY=much_secret \
    spongepowered/ore
```

If you need to migrate a production database:

```bash
$ docker run -t --link webdb:webdb \
    -e DB_USER=repo -e DB_PASSWORD=much_secret -e SECRET_KEY=much_secret \
    spongepowered/ore python3 ore/manage.py migrate

```

## Contributing

We really appreciate any and all contributions!
Contribute code with a PR or ideas with issues and/or discussion.
If you wish to discuss something that isn't a project issue, please discuss Ore in the [Sponge Web subforum](https://forums.spongepowered.org/c/sponge/sponge-web) instead.

By contributing code to Ore, you agree to license your contribution under the MIT license to this project.
You still hold copyright to your work, as detailed in the [license](https://github.com/SpongePowered/Ore/blob/master/LICENSE.txt#L4).
