# SOCcer Wrapper CLI

## Getting Started

### Prerequisites
 - SOCcer jars (`SOCcer-v1.0.jar`, `SOCcer-v2.0.jar`)
 - SOCcer models (only for SOCcer 2.0)
 - WordNet 3.1 (should be co-located with the jar in the `wordnet` directory or specified by the `gov.nih.cit.soccer.wordnet.dir` property)

### Usage
```
java -jar soccer-wrapper.jar

 -v,--model-version <arg>   SOCcer model version (default: 2.0)
 -m,--method <arg>          SOCcer method to call (estimate-runtime, validate-file, code-file)
 -i,--input-file <arg>      Path to the input file (required)
 -o,--output-file <arg>     Path to the output file (required for code-file method)
 -j,--jar-file <arg>        Path to the SOCcer jar file (required)
 -f,--model-file <arg>      Path to the SOCcer model (required for model version 2.0)
```

### Notes

This project uses Apache Ant. Run `ant` in the current directory to build the project. Output is located in the `build` directory, which should contain the `class` file as well as the executable `jar`.
