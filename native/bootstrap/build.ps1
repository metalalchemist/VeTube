$ErrorActionPreference = "Stop"
$manifest = Join-Path $PSScriptRoot "Cargo.toml"
cargo build --manifest-path $manifest --release --locked --bin bootstrap
if ($LASTEXITCODE -ne 0) { throw "Native bootstrap build failed" }
$repository = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "target/release/bootstrap.exe") -Destination (Join-Path $repository "bootstrap.exe")
