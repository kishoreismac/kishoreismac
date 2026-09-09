# Credly badges

The workflow is configured for `kiran-kumar-nune`. It fetches public badge JSON
from `https://www.credly.com/users/kiran-kumar-nune/badges.json` and displays the
latest 10 badges in the root README, linked to their public credentials.

It runs daily at 02:00 UTC or manually from **Actions > Update Badges > Run
workflow**. To change the profile, set the `CREDLY_PROFILE` repository variable
under **Settings > Secrets and variables > Actions > Variables**, or supply the
optional `credly_profile` input for one manual run. Usernames and profile URLs
(including edit URLs) are supported. Email addresses are not. Manual overrides
do not change the saved configuration.

The Python standard-library script follows all badge pages and sorts by issue
date. Accepted public badges are displayed, including expired credentials,
matching the public profile. No Credly password or separate GitHub token is
needed. Invalid profiles, network errors, empty results, and missing README
markers fail the workflow and preserve the existing README.

Changes are committed to the default branch using the built-in GitHub token.
Repository rules must allow the workflow to update that branch.

To refresh locally: `python .github/scripts/update_badges.py`.
To run regression tests: `python -m unittest discover -s .github/scripts -p "test_*.py"`.
