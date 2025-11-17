from rapidfuzz import fuzz

class FieldMatcher:
    def compare(self, doc_data, web_data):
        """Compare document and web data"""
        fields = ['applicant_name', 'vin', 'loan_amount', 'routing_no', 'account_no']
        
        matched = []
        mismatched = {}
        scores = {}
        
        for field in fields:
            doc_val = doc_data.get(field, '') or ''
            web_val = web_data.get(field, '') or ''
            
            if not doc_val and not web_val:
                scores[field] = 0
                continue
            
            if not doc_val or not web_val:
                scores[field] = 0
                mismatched[field] = {
                    'document': doc_val or 'N/A',
                    'web': web_val or 'N/A',
                    'score': 0
                }
                continue
            
            # Calculate similarity
            if field == 'applicant_name':
                score = fuzz.token_sort_ratio(str(doc_val).lower(), str(web_val).lower())
            else:
                # Clean values for comparison
                doc_clean = ''.join(c for c in str(doc_val) if c.isalnum())
                web_clean = ''.join(c for c in str(web_val) if c.isalnum())
                score = 100 if doc_clean == web_clean else 0
            
            scores[field] = score
            
            if score >= 80:
                matched.append(field)
            else:
                mismatched[field] = {
                    'document': doc_val,
                    'web': web_val,
                    'score': score
                }
        
        # Overall similarity
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        status = 'Verified' if avg_score >= 80 else 'Not Verified'
        
        return {
            'similarity_score': round(avg_score, 2),
            'status': status,
            'matched_fields': matched,
            'mismatched_fields': mismatched
        }