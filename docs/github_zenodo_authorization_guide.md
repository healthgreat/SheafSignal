# GitHub And Zenodo Authorization Guide

Timestamp: 2026-05-02 23:19:00 +08:00

## Security Rule

Do not paste GitHub or Zenodo tokens into chat. Use one of the local
authorization methods below.

## GitHub Authorization

Current local status: GitHub CLI (`gh`) has been installed as a portable
binary at:

```text
D:\BioSoft\GitHubCLI\gh_2.92.0\bin\gh.exe
```

This path has been added to the user PATH. Existing Codex/VS Code/PowerShell
sessions may need to be restarted before `gh` is found by name; until then,
Codex can call the absolute path above. The public repository now exists and
the local `origin` remote is configured:

```text
https://github.com/healthgreat/SheafSignal
```

The remaining GitHub blocker is branch push permission for workflow files.

### Option A: GitHub CLI browser login

If GitHub CLI must be reinstalled through the system package manager:

```bash
winget install --id GitHub.cli
```

Run this in a local terminal:

```bash
gh auth login --hostname github.com --git-protocol https --web
```

Then finish the browser login. After login, tell Codex: `GitHub CLI login is
done`. Codex can then create the public repository, push the branch, create a
tag, and create a release.

Recommended release settings:

```text
Repository name: SheafSignal
Visibility: Public
Release tag: v0.1.0
```

### Option A2: Local token file

If using a GitHub personal access token saved at:

```text
D:\secrets\github_token.txt
```

the token must include both scopes:

```text
repo
workflow
```

The `workflow` scope is required because this repository contains
`.github/workflows/ci.yml`. Without it, GitHub rejects the branch push even when
the token can read/write normal repository contents.

Codex can validate the token without printing it:

```bash
python scripts/check_external_release_authorization.py
```

After validation passes, Codex can run:

```bash
python scripts/publish_github_release_after_auth.py --dry-run
python scripts/publish_github_release_after_auth.py --create-release
```

### Option B: Create an empty GitHub repository manually

Create a new repository in the GitHub web UI:

```text
Repository name: SheafSignal
Visibility: Public
Initialize with README: No
Initialize with .gitignore: No
Initialize with license: No
```

Then give Codex the repository URL, for example:

```text
https://github.com/<your-user-or-organization>/SheafSignal
```

Codex can then run `git remote add`, push the branch, create the tag, and
prepare the release.

## Zenodo Authorization

Use the production Zenodo site for a final DOI. Use Zenodo Sandbox only for
testing, because sandbox DOIs are not acceptable for journal data availability.

### Option A: Manual web upload

Upload this file through the Zenodo web UI:

```text
release/archives/sheafsignal_zenodo_upload.zip
```

After publishing, copy the DOI, for example:

```text
10.5281/zenodo.xxxxxxx
```

Then tell Codex the DOI. Codex will run:

```bash
python scripts/finalize_zenodo_doi.py --doi <ZENODO_DOI>
```

### Option B: API token without posting the token in chat

Create a Zenodo personal access token with deposit permissions. Save it outside
the repository, for example:

```text
D:\secrets\zenodo_token.txt
```

Make sure this file contains only the token and is not committed to Git.

Then tell Codex:

```text
Zenodo token is saved at D:\secrets\zenodo_token.txt
```

Codex can run the upload script by reading that local file without printing the
token:

```bash
python scripts/upload_zenodo_deposition.py --publish
```

## Required Before Final Submission

1. Public GitHub repository URL.
2. Immutable Git tag and release URL.
3. Zenodo DOI.
4. DOI and GitHub URL inserted into metadata and manuscript files.
5. Final public clean-clone reproduction check.

## Remaining Author Metadata Questions

- Han Yan's email is still missing.
- ORCID IDs are optional but recommended for all authors who have them.
- CRediT roles and funding acquisition require corresponding-author
  confirmation.
- The statement "The authors declare no competing interests" requires author
  confirmation before submission.
