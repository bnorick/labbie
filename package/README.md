# Packager

# Deployment
- Verify correct branch is active
- Verify tag for version doesn't already exist
- Ensure repository is clean and branch is up to date with remote
- (Run tests)
- Build components
- (Test built components)
- For each component with version change,
  - Create patches
    - \[version_from]\_to_\[version_to].patch
    - If pre-release, create patch
      - from previous pre-release
      - from previous release
      - rollback to previous release
    - Otherwise, create patch
      - from previous release
      - from last pre-release of current version
  - Create tag
    - \[component_name.lower()]/\[version]
  - Push tag
  - Create release from tag
    - \[component_name] v\[version]
  - Add patches as assets to release
- If main component version changed and new version is a release, generate zip file and add as asset to corresponding release
