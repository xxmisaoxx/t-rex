# Publish this source package to GitHub

The archive contains repository contents: README.md, PUBLISHING.md and skills/. Extract it before uploading. Upload those contents at the repository root, preserving skills/reverse-engineering-investigator/SKILL.md. This single source tree serves every adapter; per-host export archives are not needed in the repository.

## Browser upload

1. Open your target GitHub repository.
2. Choose Add file > Upload files (an empty repository may show an uploading-an-existing-file link).
3. Drag README.md, PUBLISHING.md and the entire skills/ directory into the upload area. If extracting creates an outer folder, upload its contents rather than the outer folder or ZIP.
4. Review the file paths and enter a commit message such as Add reverse-engineering investigator v3.1.
5. Select the appropriate branch option and commit/propose the changes; complete the pull request if you chose a new branch.

If the repository already has its own root README, retain it and merge the relevant skill installation guidance instead of replacing it wholesale.

## Existing repository via Git

Clone your repository using its actual URL, then copy the extracted package contents into that clone. Preserve existing files and merge its README as appropriate. From the clone directory, use:

```sh
git switch -c add-re-investigator-v3.1
git add skills/reverse-engineering-investigator README.md PUBLISHING.md
git commit -m "Add reverse-engineering investigator v3.1"
git push -u origin add-re-investigator-v3.1
```

Open a pull request into the repository's default branch. Use your existing GitHub authentication. No credentials are included in this package.

Official instructions: https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository
