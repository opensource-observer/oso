---
description: Generate comprehensive workflow changelog from git diff analysis
allowed-tools: Bash(git*), Read, Write, Glob, Grep, Task
---

# Comprehensive Workflow Changelog Generator

!git status
!git diff --name-only HEAD~1
!git log --oneline -5

Analyze the complete workflow architecture and create a comprehensive changelog in `changelog/` directory. This command generates documentation matching the quality and depth of `changelog/18-08-2025.md`.

## Deep Analysis Requirements

### 1. Complete Workflow Architecture Analysis

- Read and analyze the ENTIRE workflow from start event to all possible end states
- Identify ALL workflow classes, mixins, routers, and tools involved
- Map complete event flow including all decision points, retry mechanisms, and branching paths
- Examine workflow inheritance patterns and mixin compositions
- Analyze all optional execution paths (execute_sql, synthesize_response flags)

### 2. Component Deep Dive

For each workflow component:

- **Primary Purpose**: What core functionality it provides
- **Key Methods**: Important methods and their roles
- **Event Handling**: What events it processes and generates
- **Dependencies**: Other components it relies on
- **Integration Points**: How it connects to other workflow parts

### 3. Flow Architecture Mapping

- **Entry Points**: All possible workflow starting events
- **Decision Trees**: Complete decision logic with all branches
- **Retry Mechanisms**: Failure handling and retry strategies
- **Optional Flows**: Conditional execution paths
- **Exit Points**: All possible workflow termination states
- **Error Handling**: Exception and failure recovery patterns

## Changelog Generation

Create `changelog/DD-MM-YYYY.md` with this EXACT structure and formatting:

### Header Format

```
# [Month Day, Year]

## [Workflow Name] - [Specific Technical Description]

[Exactly 3 lines describing technical changes compared to previous version.
Each line should be wrapped at ~80 characters using natural breaks.
Focus on concrete technical improvements, new components, or architectural
changes without marketing language.]
```

### Key Components Section

```
### Key Components

- **ComponentName**: Detailed description of component purpose, key methods,
  and integration role. Wrap lines at ~80 characters with 2-space continuation
  indent.
- **AnotherComponent**: Similar detailed description following same formatting
  pattern.
```

### Flow Elements Section

```
### Flow Elements

1. **Element Name**: Comprehensive description of what this flow element
   handles, including input events, processing logic, and output events.
2. **Next Element**: Continue with same detailed format and line wrapping.
```

### Execution Flow Section

```
### Execution Flow

[Write a comprehensive paragraph (150-200 words) explaining the complete
workflow execution from initial event through all major decision points,
optional paths, retry mechanisms, and final response generation. Include
technical details about component interactions, data flow, and architectural
patterns. Wrap lines naturally at ~80 characters.]
```

### Mermaid Diagram Requirements

Create a comprehensive mermaid diagram showing the COMPLETE workflow:

#### Diagram Completeness

- Include ALL events from start to all possible end states
- Show ALL decision points with both success/failure branches
- Include ALL retry mechanisms and loops
- Display ALL optional execution paths
- Show component method calls and event generations
- Include error handling and recovery paths

#### Color Scheme (High Contrast - Black text on light backgrounds)

```
%% Component-based color coding
style ComponentA fill:#b3e5fc,color:#000,stroke:#01579b,stroke-width:2px
style ComponentB fill:#e1bee7,color:#000,stroke:#4a148c,stroke-width:2px
style ComponentC fill:#c8e6c9,color:#000,stroke:#1b5e20,stroke-width:2px
style ComponentD fill:#ffcc80,color:#000,stroke:#e65100,stroke-width:2px
style ComponentE fill:#ffcdd2,color:#000,stroke:#b71c1c,stroke-width:2px
style ComponentF fill:#b2dfdb,color:#000,stroke:#00695c,stroke-width:2px
```

#### Diagram Structure

- Use descriptive node labels with component names and method details
- Group related operations with consistent colors
- Show data flow and event propagation clearly
- Include all conditional branches and retry loops
- Use proper mermaid syntax for complex flows
- Ensure no overlapping connections

## Formatting Standards

### Line Length and Wrapping

- Wrap all text lines at approximately 80 characters
- Use natural break points (after punctuation, conjunctions)
- Indent continuation lines with 2 spaces for list items
- Maintain consistent spacing and alignment

### Language Requirements

- Direct, concise technical language for experienced engineers
- Focus on concrete technical facts and implementation details
- Avoid marketing language, speculation, or subjective assessments
- Use present tense for describing current functionality
- Include specific method names, event types, and component interactions

### Technical Depth

- Provide sufficient detail to understand complete workflow architecture
- Include implementation-specific details (method calls, event names)
- Explain architectural patterns and component relationships
- Cover error handling and edge case behaviors
- Document configuration options and conditional behavior

## Post-Generation Tasks

After creating the changelog:

1. **Update CHANGELOG.md Index**
   Add entry in this format to changelog/CHANGELOG.md:

   ```
   - [DD-MM-YYYY](./DD-MM-YYYY.md): Brief description of workflow changes
   ```

2. **Validate Quality**
   Compare generated file against `changelog/18-08-2025.md` baseline for:
   - Comprehensiveness of mermaid diagram
   - Depth of technical analysis
   - Formatting consistency
   - Line length compliance

Generate the comprehensive workflow changelog now.
