# Collect Gradle files content
$output = @(
    Get-Content .\build.gradle.kts
    Get-Content .\app\build.gradle.kts
    Get-Content .\settings.gradle.kts
)

# Run initial build and capture output
$gradleOutput = .\gradlew assembleDebug 2>&1

# Add Gradle output for inspection
$output += $gradleOutput

# Function to extract file paths from Gradle error messages
function Get-ErrorFiles($log) {
    $pattern = 'file:///(.*?):\d+:\d+'
    $matches = [regex]::Matches($log, $pattern)
    $matches | ForEach-Object { $_.Groups[1].Value -replace '/', '\' } | Select-Object -Unique
}

# Find files from errors
$errorFiles = Get-ErrorFiles $gradleOutput

# If dependency/repo issues
if ($gradleOutput -match "Could not find|Failed to resolve|Could not resolve") {
    $output += "==== Dependency / Repo issue detected. Running clean build ===="
    $gradleOutput = .\gradlew clean build 2>&1
    $output += $gradleOutput
}

# If code/class issues
elseif ($gradleOutput -match "Unresolved reference|Overrides nothing|@Composable invocations") {
    $output += "==== Build worked, but code has unresolved references or composable issues ===="

    # Append content of files involved in errors
    foreach ($file in $errorFiles) {
        if (Test-Path $file) {
            $output += "==== Content of $file ===="
            $output += Get-Content $file
        }
    }
    $output += $gradleOutput
}
else {
    $output += "==== Build successful ===="
    $output += $gradleOutput
}

# Copy everything to clipboard
$output | clip.exe
