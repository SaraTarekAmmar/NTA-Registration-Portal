import json

class ExamAnalyzer:
    @staticmethod
    def analyze_submission(exam_content, trainee_answers):
        """
        Analyzes trainee answers against exam content.
        trainee_answers: dict { "1": "choice_label", "2": "text", ... }
        """
        results = []
        total_correct = 0
        total_questions = len(exam_content['questions'])
        
        for q in exam_content['questions']:
            q_num = str(q['number'])
            trainee_ans = trainee_answers.get(q_num, "")
            is_correct = False
            
            if q['type'] in ['choose', 'true or false']:
                is_correct = (trainee_ans == q['correct_answer'])
            elif q['type'] == 'text':
                # Text answers are usually manual, but for automation we mark as true if not empty
                # or just collect them for review. For the chart logic, we'll treat them as correct
                # if they have content.
                is_correct = len(trainee_ans) > 20 
                
            if is_correct:
                total_correct += 1
                
            results.append({
                "number": q['number'],
                "Pillar": q['metadata']['Pillar'],
                "CEFR_Level": q['metadata']['CEFR_Level'],
                "Topic": q['metadata']['Topic'],
                "Outcome": is_correct
            })
            
        score = (total_correct / total_questions) * 100 if total_questions > 0 else 0
        
        # Analytical logic from analyze_exam.py
        density = ExamAnalyzer.calculate_skill_density(results)
        ceiling = ExamAnalyzer.detect_ceiling(results)
        gaps = ExamAnalyzer.gap_analysis(results)
        summary = ExamAnalyzer.generate_narrative_summary(density, gaps, ceiling, results)
        
        # Translate density keys for the chart labels
        translations = {
            "Grammar": "القواعد والتركيب",
            "Vocabulary": "المفردات والدلالة",
            "Morphology": "الصرف والاشتقاق",
            "Comprehension": "الاستيعاب القرائي",
            "Culture": "الثقافة العامة",
            "History": "التاريخ",
            "Geography": "الجغرافيا",
            "Science": "العلوم والتكنولوجيا",
            "Nahw": "النحو",
            "Sarf": "الصرف",
            "Orthography": "الإملاء والترقيم",
            "Mufradat": "المفردات",
            "General": "عام"
        }
        ar_density = {translations.get(k, k): v for k, v in density.items()}
        
        return {
            "score": score,
            "density": ar_density,
            "ceiling": ceiling,
            "gaps": gaps,
            "summary": summary
        }

    @staticmethod
    def calculate_skill_density(data):
        pillars = {}
        for q in data:
            pillar = q['Pillar']
            if pillar not in pillars:
                pillars[pillar] = {'correct': 0, 'total': 0}
            pillars[pillar]['total'] += 1
            if q['Outcome']:
                pillars[pillar]['correct'] += 1
        
        return {p: (v['correct'] / v['total']) * 100 for p, v in pillars.items()}

    @staticmethod
    def detect_ceiling(data):
        cefr_levels = ['A1', 'A2', 'B1', 'B2', 'C1']
        level_stats = {level: {'correct': 0, 'total': 0} for level in cefr_levels}
        
        for q in data:
            level = q['CEFR_Level']
            if level in level_stats:
                level_stats[level]['total'] += 1
                if q['Outcome']:
                    level_stats[level]['correct'] += 1
                    
        ceiling = "Below A1"
        for level in cefr_levels:
            stats = level_stats[level]
            if stats['total'] > 0:
                accuracy = (stats['correct'] / stats['total']) * 100
                if accuracy > 70:
                    ceiling = level
                else:
                    break
        return ceiling

    @staticmethod
    def gap_analysis(data):
        topics = {}
        for q in data:
            topic = q['Topic']
            if topic not in topics:
                topics[topic] = {'correct': 0, 'total': 0, 'pillar': q['Pillar']}
            topics[topic]['total'] += 1
            if q['Outcome']:
                topics[topic]['correct'] += 1
                
        gaps = []
        for topic, stats in topics.items():
            failure_rate = ((stats['total'] - stats['correct']) / stats['total']) * 100
            if failure_rate > 50:
                gaps.append({'Topic': topic, 'Pillar': stats['pillar'], 'FailureRate': failure_rate})
        return gaps

    @staticmethod
    def generate_narrative_summary(density, gaps, ceiling, data):
        # Category Translation Map
        translations = {
            "Grammar": "القواعد والتركيب",
            "Vocabulary": "المفردات والدلالة",
            "Morphology": "الصرف والاشتقاق",
            "Comprehension": "الاستيعاب القرائي",
            "Culture": "الثقافة العامة",
            "History": "التاريخ",
            "Geography": "الجغرافيا",
            "Science": "العلوم والتكنولوجيا",
            "Nahw": "النحو",
            "Sarf": "الصرف",
            "Orthography": "الإملاء والترقيم",
            "Mufradat": "المفردات",
            "General": "عام"
        }

        # Professional Phrasing Templates
        phrases = {
            "high": [
                "يظهر المتقدم تمكناً لافتاً في {pillar}، مع دقة عالية في الإجابات.",
                "كفاءة ممتازة وقاعدة معرفية صلبة في {pillar}.",
                "أداء متميز يعكس استيعاباً عميقاً لأساسيات {pillar}."
            ],
            "medium": [
                "مستوى جيد إجمالاً في {pillar} مع وجود مساحة محدودة للتطوير.",
                "قدرة جيدة على التعامل مع مفاهيم {pillar} بشكل صحيح.",
                "استجابات مرضية تظهر إلماماً كافياً بمحور {pillar}."
            ],
            "low": [
                "يوجد ضعف ملحوظ في {pillar} يتطلب مراجعة وتطوير مكثف.",
                "فجوة معرفية واضحة في {pillar} قد تعيق الأداء العام.",
                "تحصيل دون المستوى المطلوب في {pillar}، يحتاج لتدخل تدريبي."
            ]
        }

        import random
        # Seed with trainee ID or something constant if possible, but here we just pick one
        # For simplicity, we'll use the score as a pseudo-index
        
        summary_parts = []
        summary_parts.append(f"📋 التقييم اللغوي والمعرفي (المستوى: {ceiling})")
        summary_parts.append("=" * 35)
        
        # 1. Strengths & Weaknesses
        summary_parts.append("\n🔍 تحليل نقاط القوة والضعف:")
        for pillar, score in density.items():
            ar_pillar = translations.get(pillar, pillar)
            idx = int(score) % 3
            if score >= 75:
                summary_parts.append(f"- {phrases['high'][idx].format(pillar=ar_pillar)}")
            elif score >= 50:
                summary_parts.append(f"- {phrases['medium'][idx].format(pillar=ar_pillar)}")
            else:
                summary_parts.append(f"- {phrases['low'][idx].format(pillar=ar_pillar)}")

        # 2. Gap Analysis
        if gaps:
            summary_parts.append("\n⚠️ محاور بحاجة لتركيز فوري:")
            for gap in gaps:
                ar_topic = translations.get(gap['Topic'], gap['Topic'])
                ar_pillar = translations.get(gap['Pillar'], gap['Pillar'])
                summary_parts.append(f"- يواجه المتقدم صعوبة في '{ar_topic}' ضمن {ar_pillar} (نسبة خطأ {gap['FailureRate']:.0f}%).")

        # 3. Final Conclusion
        avg_score = sum(density.values()) / len(density) if density else 0
        summary_parts.append("\n💡 التوصية النهائية:")
        if avg_score >= 80:
            summary_parts.append("المرشح يتمتع بخلفية معرفية ممتازة تؤهله للتميز في المراحل القادمة.")
        elif avg_score >= 60:
            summary_parts.append("أداء مقبول إجمالاً، يوصى بالتركيز على تطوير الجوانب الضعيفة المذكورة أعلاه.")
        else:
            summary_parts.append("أداء متواضع، يوصى بمراجعة مدى مواءمة المتقدم لمتطلبات البرنامج في هذا الجانب.")
                
        return "\n".join(summary_parts)
