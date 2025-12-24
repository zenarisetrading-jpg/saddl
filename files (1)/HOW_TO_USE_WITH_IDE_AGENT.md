# How to Use This Package with Your IDE Agent

## For Cursor, Windsurf, or Similar AI Coding Assistants

### Step 1: Extract the Package
```bash
unzip IMPACT_ANALYZER_FIX_PACKAGE.zip
```

### Step 2: Feed to Your IDE Agent

#### Option A: Upload All Files
1. Open your IDE (Cursor, Windsurf, etc.)
2. Start a new chat with your AI agent
3. Upload all files from IMPLEMENTATION_PACKAGE/
4. Say: "Please implement the impact analyzer fix following the instructions in README_FOR_IDE_AGENT.md"

#### Option B: Give Context Then Files
Say this to your IDE agent:

```
I need to fix our impact analyzer in a PPC optimization tool. The analyzer 
calculates before/after performance for optimization actions, but has 5 critical bugs:

1. Uses action weeks instead of upload duration for comparison periods
2. Gives credit to holds/monitors when they shouldn't get credit
3. Preventative negatives showing false "savings"
4. Isolation negatives (from harvest) getting separate credit
5. Harvest comparing all campaigns instead of just winner source

I have a complete implementation package with:
- Fixed code ready to drop in
- SQL migration script
- Test cases
- Documentation

Please read README_FOR_IDE_AGENT.md first for the overview, then implement 
following INSTRUCTIONS.md.
```

Then upload all files.

#### Option C: Step by Step
1. Upload README_FOR_IDE_AGENT.md
2. Let agent read it
3. Upload remaining files
4. Ask agent to implement following the instructions

### Step 3: Let Agent Work

Your IDE agent will:
1. ✅ Run the SQL migration
2. ✅ Replace the get_action_impact() function in db_manager.py
3. ✅ Update optimizer.py logging
4. ✅ Run tests to verify

### Step 4: Review Changes

Check that:
- [ ] db_manager.py line 1131 has the new function
- [ ] actions_log table has 4 new columns
- [ ] optimizer.py logs winner_source_campaign for harvest actions
- [ ] Test suite passes (6/6 tests)

---

## What's in the Package

| File | Purpose |
|------|---------|
| **README_FOR_IDE_AGENT.md** | Quick start for your AI agent |
| **INSTRUCTIONS.md** | Step-by-step implementation guide |
| **db_manager_get_action_impact_FIXED.py** | Complete fixed function |
| **schema_migration.sql** | Database schema changes |
| **optimizer_logging_ADDITIONS.py** | How to log winner source |
| **test_cases.py** | 6 tests to verify fix works |
| **TROUBLESHOOTING.md** | Fix common issues |
| **TECHNICAL_DETAILS.md** | How the fix works |
| **EXAMPLE_SCENARIOS.md** | Visual before/after examples |

---

## If Using Cursor Specifically

### Method 1: Chat Upload
1. Open Cursor
2. Press `Cmd/Ctrl + L` to open chat
3. Click paperclip icon to attach files
4. Upload all 9 files from IMPLEMENTATION_PACKAGE/
5. Type: "Implement following README_FOR_IDE_AGENT.md"

### Method 2: Composer
1. Press `Cmd/Ctrl + I` for Composer
2. Upload files
3. Say: "Fix the impact analyzer following the implementation package"
4. Let Composer make all the changes

---

## If Using Windsurf

1. Open Windsurf
2. Press `Cmd/Ctrl + K` for Cascade
3. Upload the package files
4. Say: "Please implement this fix following the README_FOR_IDE_AGENT.md instructions"

---

## If Using GitHub Copilot Chat

1. Open VS Code
2. Open Copilot Chat panel
3. Use `@workspace` to give context
4. Upload files using chat interface
5. Ask: "Implement the impact analyzer fix from these files"

---

## Verification Commands

After your agent implements:

```bash
# Test the database
sqlite3 your_database.db "PRAGMA table_info(actions_log);"
# Should show 4 new columns

# Run tests
python test_cases.py
# Should show 6/6 tests passing

# Check function replaced
grep -n "def get_action_impact" core/db_manager.py
# Should show the new implementation
```

---

## Timeline

- Database migration: 2 minutes
- Code changes: 5-10 minutes
- Testing: 3 minutes
- **Total: ~15 minutes with IDE agent**

---

## Troubleshooting

If agent gets stuck:
1. Point it to TROUBLESHOOTING.md
2. Ask it to check TECHNICAL_DETAILS.md for context
3. Have it run specific tests from test_cases.py

If tests fail:
1. Check TROUBLESHOOTING.md for that specific error
2. Verify database migration completed
3. Ensure all code changes were applied

---

## Questions?

The package includes:
- ✅ Complete implementation (no missing pieces)
- ✅ All code ready to drop in
- ✅ Tests to verify it works
- ✅ Troubleshooting for common issues

Your IDE agent should be able to implement this in one session (~15 min).
