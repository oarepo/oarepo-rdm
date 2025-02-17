black oarepo_rdm tests --target-version py310
autoflake --in-place --remove-all-unused-imports --recursive oarepo_rdm tests
isort oarepo_rdm tests  --profile black
