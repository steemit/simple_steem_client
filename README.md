
A simple Steem RPC client with no dependencies beyond the Python standard library.

# Project philosophy

## Minimal dependencies

Simple is better than complex.

One of the drivers for this project is horrible breakage in the Python packaging
of another Python Steem client.  This client has no Python dependencies outside
of the Python standard library.

This library should maintain compatibility with the Python 3.5, the Python version
packaged with Ubuntu 16.04 LTS.  After Ubuntu 16.04 is deprecated in 2021, this
library should continue to maintain compatibility with the Python packaged with
the oldest still-supported Ubuntu LTS release.

## Move fast, break things

Now is better than never.

This project is currently under active development.  Breaking changes to its API are
to be expected.  Development may quickly iterate and users of this library
must keep pace.

## Leverage language dynamism

Beautiful is better than ugly.  Readability counts.

Python is a dynamic language.  "Peer object" type code should be avoided, so this
codebase should not need to be upgraded in sync with steemd API changes.

## No wallet

Simple is better than complex.

`simple_steem_client` is a tool that does one thing well:  Provide a Pythonic
interface to functionality provided by `steemd`.  Wallet is separate
functionality and should be provided by a separate library.

Signing, serializing, and general handling of binary objects may be provided
by wrappers for `sign_transaction` or similar C++ standalone binaries or
API calls provided by `steemd`.  Complicated, slow, and has lots of dependencies.

Maintaining a wallet (i.e. a file of private keys created for an individual user
to control personal accounts) is out of scope for this project.  Maintaining the
security of important private keys, or the secrets used to generate such keys,
is the responsibility of the user of this library.

Since keys and secrets may be passed to binaries on the command line, and
Linux allows users to list the processes of other users, shell access to
the machine or VM running `simple_steem_client` needs to be limited to trusted
users.

## Designed for appbase

It is possible to write legacy (pre-appbase) style RPC calls with
`simple_steem_client`, but `simple_steem_client` makes no attempt
to allow the same user code to be compatible with both
pre-appbase and post-appbase servers.

It is suggested that appbase servers should be used for all client
and server code.

## No default nodes

Explicit is better than implicit.  The user must always specify the
URL of the `steemd` node(s) to connect to.
