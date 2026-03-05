# CHI Tempest Smoke Tests

This repos contains configuration and tooling to execute tempest integration tests against production sites.


# Inputs

we assume that we start with a list of sites to test, such as uc_dev, uc_prod, kvm_prod, ...

To test a site, we need to provide the following config files:
* accounts.yaml file # this defines a list of non-admin users that tempest will use to connect to the site
* tempest.conf file  # this defines properties of the site that tempest needs to configure tests, such as what features are enabled/disabled, uuids of images and networks to use,...

And the following inputs to configure which tests to run:
* include_list # a text file, each line define a regex of tests to run
* exclude_list # a text file, each line defines a rexex of tests to exclude

the exclude list takes priority over the include list.


# execution flow

when we want to run tempest tests, we'll do the following

1. create a temporary tempest "workspace"
2. copy the provided accounts.yaml and tempest.conf files into the workspace (with minimal templating so that the corect paths are populated in tempest conf)
3. copy include_list and exclude_list into the workspace
4. 

# accounts.yaml reauirements

Each site needs an `accounts.yaml.gpg` file, encrypted from a source `accounts.yaml` file.

The structure should be:
```yaml
---
- username: 'testuser-01'
  project_name: 'testing-01'
  password: password
  roles:
    - 'member'
    - 'reader'
- username: 'testuser-02'
  project_name: 'testing-02'
  password: password
  roles:
    - 'member'
    - 'reader'
- username: 'testuser-03'
  project_name: 'testing-03'
  password: password
  roles:
    - 'member'
    - 'reader'
- username: 'testuser-04'
  project_name: 'testing-04'
  password: password
  roles:
    - 'member'
    - 'reader'
```

As of tempest 46.1.0, we must set `project_name` instead of `tenant_name`, and
make sure `reader` and `member` roles are both included.

## Updating the secret for a site

To update `accounts.yaml` for a site, edit the plaintext file and re-encrypt it:

```sh
export SECRET_PASSPHRASE="<the passphrase>"
./crypt_secret.sh encrypt path/to/accounts.yaml path/to/accounts.yaml.gpg
```

Then commit the updated `accounts.yaml.gpg`. Never commit the plaintext `accounts.yaml`.
