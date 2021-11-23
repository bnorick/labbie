You need tesseract at `bin/tesseract`.

To deploy, you need the (closed source) `labbie_admin` repository checked out in a sibling directory to this repo. You also need to `poetry install  -E deploy` for the `package` package.

Commands of interest:
- From labbie dir, `poetry run labbie --debug --force` (in two command prompts) will let you relaunch easily with code changes
- From package dir, `poetry run build` followed (optionally) by `poetry run deploy` for packaging