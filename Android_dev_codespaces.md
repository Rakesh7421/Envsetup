# CODESPACES
## JAVA AND ANDOID HOME, SDK, COMMANDLINETOOLS and REMOVE OLD JAVA 25.0.1
```
#!/usr/bin/env bash
set -e

TARGET_VERSION="25.0.1"

echo "==> Listing all Java versions installed:"
for j in $(which -a java); do
    echo "$j -> $($j -version 2>&1 | head -n 1)"
done

echo "==> Removing any references to version $TARGET_VERSION..."

# Remove from PATH / environment files
for file in "$HOME/.bashrc" "$HOME/.zshrc"; do
  if grep -q "$TARGET_VERSION" "$file"; then
    echo "==> Removing $TARGET_VERSION references from $file"
    sed -i "/$TARGET_VERSION/d" "$file"
  fi
done

# Remove from local.properties
if [ -f local.properties ] && grep -q "$TARGET_VERSION" local.properties; then
  echo "==> Removing $TARGET_VERSION from local.properties"
  sed -i "/$TARGET_VERSION/d" local.properties
fi

# Remove any directories with 25.0.1 under JDK or Android SDK
for dir in $(find /usr/lib/jvm "$HOME/android-sdk" -type d -name "*$TARGET_VERSION*" 2>/dev/null); do
  echo "==> Deleting directory $dir"
  sudo rm -rf "$dir"
done

# Remove any java symlinks pointing to 25.0.1
for java_path in $(which -a java); do
  if readlink -f "$java_path" | grep -q "$TARGET_VERSION"; then
    echo "==> Removing symlink $java_path pointing to $TARGET_VERSION"
    sudo rm -f "$java_path"
  fi
done

### CONFIG
JAVA_HOME_DIR="/usr/lib/jvm/java-17-openjdk-amd64"
SDK_DIR="$HOME/android-sdk"
CMDLINE_ZIP="commandlinetools-linux-11076708_latest.zip"
CMDLINE_URL="https://dl.google.com/android/repository/${CMDLINE_ZIP}"
BASHRC="$HOME/.bashrc"
ZSHRC="$HOME/.zshrc"

echo "==> Starting Java + Android SDK setup"

########################################
# JAVA 17 (IDEMPOTENT)
########################################

echo "==> Ensuring OpenJDK 17 is installed"
if ! java -version 2>&1 | grep -q "17."; then
  sudo apt update
  sudo apt install -y openjdk-17-jdk
else
  echo "==> OpenJDK 17 already installed"
fi

echo "==> Setting Java 17 as default (safe override)"
sudo update-alternatives --set java "$JAVA_HOME_DIR/bin/java" || true
sudo ln -sf "$JAVA_HOME_DIR/bin/java" /usr/bin/java

# Persist JAVA_HOME + PATH once in Bash
grep -q "JAVA_HOME=$JAVA_HOME_DIR" "$BASHRC" || cat <<EOF >> "$BASHRC"

# Java 17
export JAVA_HOME=$JAVA_HOME_DIR
export PATH=\$JAVA_HOME/bin:\$PATH
EOF

# Persist JAVA_HOME + PATH once in Zsh
grep -q "JAVA_HOME=$JAVA_HOME_DIR" "$ZSHRC" || cat <<EOF >> "$ZSHRC"

# Java 17
export JAVA_HOME=$JAVA_HOME_DIR
export PATH=\$JAVA_HOME/bin:\$PATH
EOF

# Apply environment variables now
export JAVA_HOME="$JAVA_HOME_DIR"
export PATH="$JAVA_HOME/bin:$PATH"

echo "==> Java version in use:"
java -version

########################################
# ANDROID SDK (IDEMPOTENT)
########################################

echo "==> Setting up Android SDK at $SDK_DIR"
mkdir -p "$SDK_DIR"

if [ ! -d "$SDK_DIR/cmdline-tools/latest" ]; then
  echo "==> Installing Android command-line tools"
  cd "$SDK_DIR"
  if [ ! -f "$CMDLINE_ZIP" ]; then
    wget "$CMDLINE_URL"
  fi
  unzip -o "$CMDLINE_ZIP"
  mkdir -p cmdline-tools/latest
  mv cmdline-tools/* cmdline-tools/latest/ || true
else
  echo "==> Android command-line tools already installed"
fi

# Persist Android SDK environment variables in Bash
grep -q "ANDROID_SDK_ROOT=$SDK_DIR" "$BASHRC" || cat <<EOF >> "$BASHRC"

# Android SDK
export ANDROID_SDK_ROOT=$SDK_DIR
export ANDROID_HOME=\$ANDROID_SDK_ROOT
export PATH=\$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:\$ANDROID_SDK_ROOT/platform-tools:\$PATH
EOF

# Persist Android SDK environment variables in Zsh
grep -q "ANDROID_SDK_ROOT=$SDK_DIR" "$ZSHRC" || cat <<EOF >> "$ZSHRC"

# Android SDK
export ANDROID_SDK_ROOT=$SDK_DIR
export ANDROID_HOME=\$ANDROID_SDK_ROOT
export PATH=\$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:\$ANDROID_SDK_ROOT/platform-tools:\$PATH
EOF

# Apply environment variables now
export ANDROID_SDK_ROOT="$SDK_DIR"
export ANDROID_HOME="$SDK_DIR"
export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"

echo "==> Installing Android SDK packages"
yes | sdkmanager --licenses
sdkmanager \
  "platform-tools" \
  "platforms;android-34" \
  "build-tools;34.0.0"

########################################
# PROJECT WIRING
########################################

echo "==> Writing local.properties"
echo "sdk.dir=$SDK_DIR" > local.properties

echo "==> Resetting Gradle"
./gradlew --stop || true
./gradlew clean

echo "==> Setup complete. Restart the shell session:"
echo "    source ~/.bashrc"
echo "    source ~/.zshrc"
restarting the machine session"
source ~/.bashrc
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```
