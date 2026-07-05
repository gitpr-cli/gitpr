# Technical Documentation: Code Archaeologist with Git Blame (--blame)

GitPR's **Code Archaeologist** uses `git blame` combined with artificial intelligence to trace the origin and evolution of business rules in your code. It classifies each commit as **ORIGIN** (rule creation) or **REFACTORING** (later modification) and generates a detailed timeline.

---

## 1. Syntax and Formats

### 1.1 Direct Mode (specific lines)

```bash
gitpr -b src/core.py:140-195    # Line range
gitpr -b src/main.py:42          # Single line
```

### 1.2 Interactive Mode

```bash
gitpr -b src/core.py             # GitPR will ask which lines
```

The terminal will display:
```
📂 Selected file: src/core.py
Which lines do you want to investigate? (E.g.: 10-20 or just 45)
```

---

## 2. How It Works

1. **`git blame`** captures the author, date, and hash of each line in the specified range
2. AI **classifies** each commit as `ORIGIN` (created the business rule) or `REFACTORING` (modified existing code)
3. The engine traces up to **4 levels of parent commits** to understand the complete evolution
4. The result is displayed in the terminal (color-coded) and saved as a Markdown report

### Terminal Output

- 🟢 **Green** = ORIGIN commit
- 🟡 **Yellow** = REFACTORING commit

---

## 3. Integration with Issues

The Archaeologist can feed the generation of **Technical Debt Issues**:

```bash
gitpr -is -b src/legacy/parser.py:200-350
```

In this mode, the AI generates an issue explaining **how the block evolved** and **why it needs to be refactored**, using the blame chronology as context.

---

## 4. AI Provider Selection

```bash
gitpr -b file.py:10-50 -p gemini
gitpr -b file.py:10-50 -p deepseek
```

> **Note:** The Archaeologist uses the **secondary** model (cheaper) for commit classification and the **primary** model (advanced) for the final executive summary, optimizing quota consumption.
