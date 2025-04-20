# AI Executive Team Checkpoints

This directory contains checkpoints of the AI Executive Team project at various stages of development.

## Available Checkpoints

- **checkpoint_2025-04-12_1603**: Basic dashboard with agent management, knowledge base, and communication channel settings (Slack and Telegram)

## How to Restore a Checkpoint

### Using PowerShell Script

```powershell
cd checkpoints
.\restore_checkpoint.ps1 -CheckpointName "checkpoint_2025-04-12_1603"
```

### Manual Restoration

1. Stop any running Flask processes
2. Backup your current files if needed
3. Copy the files from the checkpoint directory to the main project directory:
   ```
   copy checkpoint_NAME\run_dashboard.py ..\ /Y
   xcopy /E /I /Y checkpoint_NAME\web_dashboard ..\web_dashboard
   ```

## Creating New Checkpoints

When implementing major new features, it's recommended to create a new checkpoint:

1. Create a new directory with a timestamp: `mkdir checkpoint_YYYY-MM-DD_HHMM`
2. Copy the current project files:
   ```
   copy ..\run_dashboard.py checkpoint_YYYY-MM-DD_HHMM\ /Y
   xcopy /E /I /Y ..\web_dashboard checkpoint_YYYY-MM-DD_HHMM\web_dashboard
   ```
3. Create a README.md file documenting the current state and features
