```mermaid
flowchart TD
    %% Main CLI Entry Point
    LCS_CLI[lcs CLI<br/>Entry Point]

    %% Core Commands
    subgraph "Core Commands"
        Init[lcs init<br/>Initialize project<br/>with AI agent templates]
        Check[lcs check<br/>Verify AI agent<br/>and tool installation]
    end

    %% Extension Commands
    subgraph "Extension Commands"
        ExtList[lcs extension list<br/>List installed extensions]
        ExtSearch[lcs extension search<br/>Search extension catalog]
        ExtInfo[lcs extension info<br/>Show extension details]
        ExtAdd[lcs extension add<br/>Install extension]
        ExtRemove[lcs extension remove<br/>Uninstall extension]
        ExtUpdate[lcs extension update<br/>Update extensions]
        ExtEnable[lcs extension enable<br/>Enable extension]
        ExtDisable[lcs extension disable<br/>Disable extension]
    end

    %% Agent Commands (generated)
    subgraph "AI Agent Commands"
        Constitution[/lcs.charter<br/>Create project principles]
        Specify[/lcs.define<br/>Define requirements]
        Clarify[/lcs.refine<br/>Clarify specifications]
        Plan[/lcs.design<br/>Create technical plans]
        Tasks[/lcs.sequence<br/>Generate task lists]
        Implement[/lcs.author<br/>Execute implementation]
        Analyze[/lcs.audit<br/>Analyze consistency]
        Checklist[/lcs.rubric<br/>Create quality checklists]
    end

    %% Extension Commands (dynamic)
    subgraph "Extension Commands (Dynamic)"
        JiraSpecToIssues[/lcs.jira.specstoissues<br/>Create Jira issues from specs]
        JiraDiscoverFields[/lcs.jira.discover-fields<br/>Discover Jira custom fields]
        JiraSyncStatus[/lcs.jira.sync-status<br/>Sync task status]
    end

    %% CLI Structure
    LCS_CLI --> Init
    LCS_CLI --> Check
    LCS_CLI --> ExtList
    LCS_CLI --> ExtSearch
    LCS_CLI --> ExtInfo
    LCS_CLI --> ExtAdd
    LCS_CLI --> ExtRemove
    LCS_CLI --> ExtUpdate
    LCS_CLI --> ExtEnable
    LCS_CLI --> ExtDisable

    %% Template Generation Flow
    Init --> Constitution
    Init --> Specify
    Init --> Clarify
    Init --> Plan
    Init --> Tasks
    Init --> Implement
    Init --> Analyze
    Init --> Checklist

    %% Extension Flow
    ExtAdd --> JiraSpecToIssues
    ExtAdd --> JiraDiscoverFields
    ExtAdd --> JiraSyncStatus

    %% Command Dependencies
    Constitution -.-> Specify
    Specify -.-> Clarify
    Clarify -.-> Plan
    Plan -.-> Tasks
    Tasks -.-> Implement
    Implement -.-> Analyze
    Analyze -.-> Checklist

    %% Styling
    classDef coreCommands fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef extensionCommands fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef agentCommands fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef dynamicCommands fill:#fff3e0,stroke:#f57c00,stroke-width:2px

    class LCS_CLI,Init,Check coreCommands
    class ExtList,ExtSearch,ExtInfo,ExtAdd,ExtRemove,ExtUpdate,ExtEnable,ExtDisable extensionCommands
    class Constitution,Specify,Clarify,Plan,Tasks,Implement,Analyze,Checklist agentCommands
    class JiraSpecToIssues,JiraDiscoverFields,JiraSyncStatus dynamicCommands
```
