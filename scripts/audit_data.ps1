param(
    [string]$OutputPath = "reports/data_audit.md"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$datasets = @(
    @{ Name = "English places"; Path = Join-Path $root "egypt_places_english.csv"; Kind = "places_en" },
    @{ Name = "Arabic places"; Path = Join-Path $root "egypt_places_arabic.csv"; Kind = "places_ar" },
    @{ Name = "English ticket prices"; Path = Join-Path $root "ticket_prices_english.csv"; Kind = "tickets_en" },
    @{ Name = "Arabic ticket prices"; Path = Join-Path $root "ticket_prices_arabic.csv"; Kind = "tickets_ar" }
)

function Get-ColumnValue {
    param(
        [object]$Row,
        [string]$ColumnName
    )

    if ([string]::IsNullOrWhiteSpace($ColumnName)) {
        return $null
    }

    return $Row.PSObject.Properties[$ColumnName].Value
}

function Measure-Dataset {
    param(
        [hashtable]$Dataset
    )

    if (-not (Test-Path -LiteralPath $Dataset.Path)) {
        return [pscustomobject]@{
            Name = $Dataset.Name
            Path = $Dataset.Path
            Rows = 0
            Columns = ""
            MissingPrimaryName = "missing file"
            DuplicatePrimaryName = "missing file"
            MissingPrice = "n/a"
        }
    }

    $rows = @(Import-Csv -LiteralPath $Dataset.Path -Encoding UTF8)
    $columns = @()
    if ($rows.Count -gt 0) {
        $columns = @($rows[0].PSObject.Properties.Name)
    }

    $primaryNameColumn = $columns[0]
    $priceColumn = $null

    if ($Dataset.Kind -eq "places_en") {
        $primaryNameColumn = "name"
        $priceColumn = "price_egp"
    }
    elseif ($Dataset.Kind -eq "tickets_en") {
        $primaryNameColumn = "site_name"
        $priceColumn = "foreign_egp"
    }
    elseif ($Dataset.Kind -eq "places_ar") {
        $primaryNameColumn = $columns[0]
        $priceColumn = $columns[$columns.Count - 1]
    }
    elseif ($Dataset.Kind -eq "tickets_ar") {
        $primaryNameColumn = $columns[0]
        $priceColumn = $columns[5]
    }

    $names = @($rows | ForEach-Object { (Get-ColumnValue $_ $primaryNameColumn).ToString().Trim() })
    $missingNames = @($names | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count
    $duplicateNames = @(
        $names |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Group-Object |
            Where-Object { $_.Count -gt 1 }
    ).Count

    $missingPrice = "n/a"
    if (-not [string]::IsNullOrWhiteSpace($priceColumn)) {
        $missingPrice = @(
            $rows | Where-Object {
                $value = Get-ColumnValue $_ $priceColumn
                [string]::IsNullOrWhiteSpace($value)
            }
        ).Count
    }

    return [pscustomobject]@{
        Name = $Dataset.Name
        Path = $Dataset.Path
        Rows = $rows.Count
        Columns = ($columns -join ", ")
        MissingPrimaryName = $missingNames
        DuplicatePrimaryName = $duplicateNames
        MissingPrice = $missingPrice
    }
}

$results = @($datasets | ForEach-Object { Measure-Dataset $_ })

$reportDir = Split-Path -Parent (Join-Path $root $OutputPath)
if (-not (Test-Path -LiteralPath $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}

$lines = @()
$lines += "# Data Audit"
$lines += ""
$lines += "Generated from the current CSV files in the project workspace."
$lines += ""
$lines += "| Dataset | Rows | Missing primary names | Duplicate primary names | Missing selected price |"
$lines += "|---|---:|---:|---:|---:|"
foreach ($result in $results) {
    $lines += "| $($result.Name) | $($result.Rows) | $($result.MissingPrimaryName) | $($result.DuplicatePrimaryName) | $($result.MissingPrice) |"
}
$lines += ""
$lines += "## Columns"
$lines += ""
foreach ($result in $results) {
    $lines += "### $($result.Name)"
    $lines += ""
    $lines += $result.Columns
    $lines += ""
}
$lines += "## Step 1 decision"
$lines += ""
$lines += "Use the English places file as the backend-friendly v1 source of truth, and load the matching Arabic places file alongside it for bilingual display fields. Both places files now contain the same 1,258 rows."

$fullOutputPath = Join-Path $root $OutputPath
Set-Content -LiteralPath $fullOutputPath -Value $lines -Encoding UTF8
Write-Output "Wrote $fullOutputPath"
