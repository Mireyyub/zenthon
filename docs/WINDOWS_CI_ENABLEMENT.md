# Windows CI Enablement Note

The currently authenticated repository automation identity can create feature branches and pull requests, but it **cannot write to `.github/workflows/`**. The Windows package job therefore remains deliberately outside pull request [#2](https://github.com/Mireyyub/zenthon/pull/2), rather than being presented as CI that has already run.

After a maintainer grants an identity with the GitHub `workflows` permission, add the following job under `jobs:` in `.github/workflows/ci-cd.yml`. It builds the full Windows release profile, runs the packaged core and loopback bridge smoke checks, and uploads only the resulting installer artifact.

```yaml
windows-package:
  name: Windows Desktop Package
  needs: [test]
  runs-on: windows-latest
  steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install NSIS
      run: choco install nsis --no-progress --yes

    - name: Build installer and run packaged smoke checks
      shell: pwsh
      run: ./scripts/build_windows.ps1 -Installer

    - name: Upload Windows installer
      uses: actions/upload-artifact@v4
      with:
        name: Zenthon-Setup-Windows
        path: dist/Zenthon-Setup.exe
        if-no-files-found: error
```

| Release control | Behaviour |
|---|---|
| Build input | `requirements-full.txt` plus the PyInstaller build requirements |
| Executable validation | `Zenthon.exe --smoke` validates the canonical core path without showing a GUI |
| Bridge validation | `Zenthon.exe --bridge-smoke` opens a dynamically allocated loopback API port, calls the root endpoint, and stops it cleanly |
| Installer output | `dist/Zenthon-Setup.exe` is uploaded only after the two smoke steps succeed |
| Remaining manual gate | A real Windows 11 system must still check installer UI, first-run profile UI, uninstall behaviour, and organisation-specific code-signing or allowlist rules |
