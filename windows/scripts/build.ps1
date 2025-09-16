# Requires: Visual Studio 2022 Build Tools with CMake integration.
param(
    [string]$Configuration = "Release"
)

$buildDir = Join-Path $PSScriptRoot "..\build"
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
}

cmake -S .. -B $buildDir -G "Visual Studio 17 2022"
cmake --build $buildDir --config $Configuration
