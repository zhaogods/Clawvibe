param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsFromCaller
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$entry = Join-Path $scriptDir "analyze_repo.py"

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -B $entry @ArgsFromCaller
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -B $entry @ArgsFromCaller
    exit $LASTEXITCODE
}

Write-Error "Python was not found in PATH."
exit 1

