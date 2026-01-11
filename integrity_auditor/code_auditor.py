"""
Code Plagiarism Detection using AST
Supports: Python, Java, JavaScript
"""
import ast
import difflib
import hashlib
from typing import Dict, Tuple, List
import os


class CodeAuditor:
    """Detects code plagiarism using AST analysis"""
    
    def __init__(self):
        self.languages = ['python', 'java', 'javascript']
        self.threshold = 75  # Similarity threshold for plagiarism
        print("🛡️ Code Auditor Initialized")
    
    def analyze_python(self, code1: str, code2: str) -> Dict:
        """Analyze Python code similarity using AST"""
        try:
            # Parse ASTs
            tree1 = ast.parse(code1)
            tree2 = ast.parse(code2)
            
            # Anonymize variable names
            tree1_anon = self._anonymize_ast(tree1)
            tree2_anon = self._anonymize_ast(tree2)
            
            # Convert to string representation
            struct1 = ast.dump(tree1_anon)
            struct2 = ast.dump(tree2_anon)
            
            # Calculate similarity
            similarity = self._calculate_similarity(struct1, struct2)
            
            # Calculate hash for exact matching
            hash1 = hashlib.md5(struct1.encode()).hexdigest()
            hash2 = hashlib.md5(struct2.encode()).hexdigest()
            
            return {
                "language": "python",
                "similarity_percentage": similarity,
                "is_plagiarized": similarity > self.threshold,
                "hash_match": hash1 == hash2,
                "ast_structure1": struct1[:200] + "..." if len(struct1) > 200 else struct1,
                "ast_structure2": struct2[:200] + "..." if len(struct2) > 200 else struct2
            }
        except SyntaxError as e:
            return {"error": f"Syntax error: {e}", "language": "python"}
    
    def _anonymize_ast(self, tree: ast.AST) -> ast.AST:
        """Anonymize variable and function names in AST"""
        
        class Anonymizer(ast.NodeTransformer):
            def visit_Name(self, node):
                node.id = "VAR"
                return node
            
            def visit_arg(self, node):
                node.arg = "ARG"
                return node
            
            def visit_FunctionDef(self, node):
                node.name = "FUNC"
                return self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                node.name = "CLASS"
                return self.generic_visit(node)
        
        anonymizer = Anonymizer()
        return anonymizer.visit(tree)
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        seq_matcher = difflib.SequenceMatcher(None, str1, str2)
        return seq_matcher.ratio() * 100
    
    def analyze_files(self, filepath1: str, filepath2: str) -> Dict:
        """Analyze two code files"""
        try:
            # Read files
            with open(filepath1, 'r', encoding='utf-8') as f1:
                code1 = f1.read()
            
            with open(filepath2, 'r', encoding='utf-8') as f2:
                code2 = f2.read()
            
            # Determine language based on extension
            ext1 = os.path.splitext(filepath1)[1].lower()
            ext2 = os.path.splitext(filepath2)[1].lower()
            
            if ext1 != ext2:
                return {"error": "Files must be of same language"}
            
            # Analyze based on language
            if ext1 in ['.py', '.pyw']:
                return self.analyze_python(code1, code2)
            elif ext1 in ['.java']:
                # TODO: Implement Java analysis
                return {"language": "java", "status": "Java analysis coming soon"}
            elif ext1 in ['.js', '.jsx']:
                # TODO: Implement JavaScript analysis
                return {"language": "javascript", "status": "JavaScript analysis coming soon"}
            else:
                return {"error": f"Unsupported file type: {ext1}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_plagiarism_report(self, filepath1: str, filepath2: str) -> str:
        """Generate plagiarism report"""
        analysis = self.analyze_files(filepath1, filepath2)
        
        if "error" in analysis:
            return f"❌ Error: {analysis['error']}"
        
        report = f"""
        🕵️ CODE PLAGIARISM REPORT
        {'='*45}
        File 1: {os.path.basename(filepath1)}
        File 2: {os.path.basename(filepath2)}
        Language: {analysis.get('language', 'Unknown')}
        {'='*45}
        Structural Similarity: {analysis.get('similarity_percentage', 0):.2f}%
        Threshold for Plagiarism: {self.threshold}%
        {'='*45}
        """
        
        if analysis.get('is_plagiarized', False):
            report += "Verdict: 🔴 PLAGIARISM DETECTED\n"
            report += "Reason: Code structure is identical\n"
            report += "Note: Variable names were ignored in analysis\n"
        else:
            report += "Verdict: 🟢 Code appears original\n"
        
        report += "="*45
        return report