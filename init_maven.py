import argparse
from pathlib import Path
import textwrap


POM_TEMPLATE = textwrap.dedent(
    """\
    <?xml version="1.0" encoding="UTF-8"?>
    <project xmlns="http://maven.apache.org/POM/4.0.0"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.example</groupId>
        <artifactId>jtesterai</artifactId>
        <version>1.0-SNAPSHOT</version>

        <!-- Core project coordinates -->
        <properties>
            <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
            <maven.compiler.source>17</maven.compiler.source>
            <maven.compiler.target>17</maven.compiler.target>
            <junit.jupiter.version>5.10.2</junit.jupiter.version>
            <mockito.version>5.11.0</mockito.version>
            <maven-surefire-plugin.version>3.2.5</maven-surefire-plugin.version>
        </properties>

        <dependencies>
            <!-- JUnit 5 API + engine; needed so Maven can discover and run tests -->
            <dependency>
                <groupId>org.junit.jupiter</groupId>
                <artifactId>junit-jupiter</artifactId>
                <version>${junit.jupiter.version}</version>
                <scope>test</scope>
            </dependency>
            <!-- Mockito core for mocking; used by generated tests -->
            <dependency>
                <groupId>org.mockito</groupId>
                <artifactId>mockito-core</artifactId>
                <version>${mockito.version}</version>
                <scope>test</scope>
            </dependency>
            <!-- Mockito extension that integrates with JUnit 5 @ExtendWith -->
            <dependency>
                <groupId>org.mockito</groupId>
                <artifactId>mockito-junit-jupiter</artifactId>
                <version>${mockito.version}</version>
                <scope>test</scope>
            </dependency>
        </dependencies>

        <build>
            <plugins>
                <!-- Surefire runs unit tests during `mvn test`; useModulePath=false
                     avoids module-path quirks and keeps classpath resolution simple -->
                <plugin>
                    <groupId>org.apache.maven.plugins</groupId>
                    <artifactId>maven-surefire-plugin</artifactId>
                    <version>${maven-surefire-plugin.version}</version>
                    <configuration>
                        <!-- JUnit 5 -->
                        <useModulePath>false</useModulePath>
                    </configuration>
                </plugin>
            </plugins>
        </build>
    </project>
    """
).strip() + "\n"


def ensure_directories(project_root: Path) -> None:
    """Make sure the Maven src tree exists so mvn can run immediately."""
    for subdir in ("src/main/java", "src/test/java"):
        path = project_root / subdir
        path.mkdir(parents=True, exist_ok=True)


def write_pom(project_root: Path, force: bool = False) -> None:
    pom_path = project_root / "pom.xml"
    if pom_path.exists() and not force:
        print(f"ℹ️ pom.xml already exists at {pom_path}. Use --force to overwrite.")
        return

    pom_path.write_text(POM_TEMPLATE, encoding="utf-8")
    print(f"✅ Wrote Maven descriptor to {pom_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Create a baseline pom.xml with JUnit 5 and Mockito."
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Root of the Java project (default: current directory).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing pom.xml if present.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    ensure_directories(project_root)
    write_pom(project_root, force=args.force)

    print("📦 Maven scaffold ready. You can now run `mvn test` or `python executor.py`.")


if __name__ == "__main__":
    main()

