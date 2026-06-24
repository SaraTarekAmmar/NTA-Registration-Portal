(function () {
  "use strict";

  function crit(key, ar, en, weight) {
    return {
      key: key,
      title_ar: ar,
      title_en: en || "",
      weight: weight || 1,
      scale_min: 1,
      scale_max: 5,
      required: true
    };
  }

  var commonFive = [
    crit("appearance", "المظهر العام", "Appearance"),
    crit("motivation_enthusiasm", "الحماس والرغبة في المشاركة", "Willingness to participate and enthusiasm"),
    crit("self_confidence", "الثقة بالنفس", "Self-confidence"),
    crit("initiative", "المبادرة", "Initiation"),
    crit("communication_skills", "مهارات التواصل", "Communication skills")
  ];

  var adultTen = commonFive.concat([
    crit("personality", "تقييم الشخصية", "Personality"),
    crit("ability_to_express", "القدرة على التعبير عن نفسه بوضوح", "Ability to express himself clearly"),
    crit("problem_solving", "حل المشكلات", "Problem-solving"),
    crit("analytical_skills", "المهارات التحليلية", "Analytical skills"),
    crit("career_goals", "الطموحات العملية", "Career goals")
  ]);

  var executiveFifteen = adultTen.concat([
    crit("presentation_skills", "مهارات العرض", "Presentation skills"),
    crit("leadership", "القيادة", "Leadership"),
    crit("creativity", "الإبداع", "Creativity"),
    crit("decision_making", "اتخاذ القرار", "Decision making"),
    crit("flexibility_adaptability", "المرونة والقدرة على التكيف", "Flexibility/adaptability")
  ]);

  var youthTen = [
    crit("appearance", "المظهر العام", "Appearance"),
    crit("conversing_interacting", "أسلوبه في الحديث والتواصل", "Manner of conversing and interacting"),
    crit("motivation_enthusiasm", "الحماس والرغبة في المشاركة", "Willingness to participate and enthusiasm"),
    crit("self_confidence", "الثقة بالنفس", "Self-confidence"),
    crit("collaboration_teamwork", "التعاون والقدرة على العمل الجماعي", "Collaboration and teamwork"),
    crit("respect_dialogue", "احترامه للآخرين وأسلوبه في الحوار", "Respect for others and style of dialogue"),
    crit("ability_to_express", "قدرته على التعبير عن نفسه بوضوح", "Ability to express himself clearly"),
    crit("responsiveness_guidance", "مرونته واستجابته للتوجيهات", "Flexibility and responsiveness to guidance"),
    crit("general_behavior", "سلوكه العام - هدوءه أو اندفاعه", "General behavior"),
    crit("hobbies_interests", "وجود هوايات أو اهتمامات خاصة", "Hobbies or interests")
  ];

  function interviewForm(criteria, opts) {
    opts = opts || {};
    return {
      enabled: true,
      version: 1,
      source: opts.source || "scenario_template",
      score_scale: { min: 1, max: 5, labels: ["ضعيف", "مقبول", "جيد", "جيد جداً", "ممتاز"] },
      criteria: criteria,
      total_max: criteria.length * 5,
      pass_threshold: opts.pass_threshold || Math.ceil(criteria.length * 5 * 0.6),
      require_committee_members: true,
      require_notes: true,
      final_recommendations: ["accept", "waitlist", "unsuitable"],
      fixed_criteria_keys: commonFive.map(function (c) { return c.key; })
    };
  }

  function step(order, type, title, description, config) {
    return {
      step_key: "step_" + order,
      step_type: type,
      title_ar: title,
      description_ar: description || "",
      step_order: order - 1,
      is_required: true,
      config_json: Object.assign({
        is_active: true,
        transition_pass: "next",
        transition_fail: "reject"
      }, config || {})
    };
  }

  function finalDecision(order) {
    return step(order, "acceptance_decision", "القرار النهائي", "اعتماد النتيجة النهائية وإلحاق المقبولين بالبرنامج.", {
      transition_pass: "accept",
      transition_fail: "reject",
      final_decision: { allow_waitlist: true, require_reason_when_unsuitable: true }
    });
  }

  function buildIndividual() {
    return [
      step(1, "admin_review", "مراجعة التسجيل والمستندات", "مطابقة البيانات والمرفقات قبل بدء مراحل القبول."),
      step(2, "background_check", "الاستعلام الأمني", "مراجعة داخلية لا تظهر أسبابها للمتقدم عند الرفض.", { silent_rejection: true }),
      step(3, "admission_test", "الاختبار النفسي", "تقييم نفسي أو قدرات حسب البرنامج."),
      step(4, "admission_test", "اختبارات المعلومات العامة واللغة", "الاختبارات المعرفية واللغوية المطلوبة."),
      step(5, "interview", "المقابلة الأولى", "نموذج مقابلة من 10 محاور.", { interview_form: interviewForm(adultTen, { pass_threshold: 30 }) }),
      step(6, "interview", "المقابلة الثانية", "نموذج مقابلة نهائي من 15 محوراً عند الحاجة.", { interview_form: interviewForm(executiveFifteen, { pass_threshold: 45 }) }),
      finalDecision(7)
    ];
  }

  function buildPlpJplp() {
    return [
      step(1, "admin_review", "مراجعة التسجيل والمستندات", "مراجعة أهلية أولية."),
      step(2, "background_check", "الاستعلام الأمني", "استعلام داخلي صامت عند الرفض.", { silent_rejection: true }),
      step(3, "admission_test", "اختبارات القبول", "اختبارات البرنامج المطلوبة."),
      step(4, "interview", "المقابلة الشخصية", "نموذج PLP/JPLP من 10 محاور.", { interview_form: interviewForm(adultTen, { pass_threshold: 30 }) }),
      step(5, "admin_review", "مراجعة اللجنة", "تجميع النتائج واعتماد التوصية."),
      finalDecision(6)
    ];
  }

  function buildExecutive() {
    return [
      step(1, "admin_review", "مراجعة التسجيل والمستندات", "مراجعة المستندات والخبرة العملية."),
      step(2, "background_check", "الاستعلام الأمني", "استعلام داخلي صامت عند الرفض.", { silent_rejection: true }),
      step(3, "admission_test", "اختبارات القبول", "اختبارات المعرفة واللغة والتحليل."),
      step(4, "interview", "المقابلة الأولى", "نموذج مقابلة من 15 محوراً.", { interview_form: interviewForm(executiveFifteen, { pass_threshold: 45 }) }),
      step(5, "interview", "المقابلة النهائية", "توصية اللجنة النهائية من 15 محوراً.", { interview_form: interviewForm(executiveFifteen, { pass_threshold: 45 }) }),
      step(6, "admission_test", "التقييم القبلي", "تقييم قبلي قبل بدء البرنامج.", { pre_assessment: true }),
      finalDecision(7)
    ];
  }

  function buildYouth() {
    return [
      step(1, "admin_review", "مراجعة التسجيل والمستندات", "مراجعة أهلية الشباب المتقدمين."),
      step(2, "background_check", "الاستعلام الأمني", "استعلام داخلي صامت عند الرفض.", { silent_rejection: true }),
      step(3, "interview", "المقابلة الشخصية", "نموذج مقابلة الشباب من 10 محاور.", { interview_form: interviewForm(youthTen, { pass_threshold: 30 }) }),
      step(4, "admin_review", "مراجعة اللجنة", "تجميع تقييمات اللجنة واعتماد التوصية."),
      finalDecision(5)
    ];
  }

  function buildNominee() {
    return [
      step(1, "admin_review", "مطابقة الترشيح الرسمي", "مطابقة بيانات المتقدم مع القائمة الرسمية للجهة المرشحة.", {
        nominee_flow: true,
        require_nomination_list_match: true
      }),
      step(2, "admin_review", "مراجعة المستندات", "مراجعة اكتمال الملف والمرفقات."),
      step(3, "background_check", "الاستعلام الأمني", "استعلام داخلي صامت عند الرفض.", { silent_rejection: true }),
      finalDecision(4)
    ];
  }

  var templates = {
    individual_default: {
      label_ar: "متقدم فردي - مسار كامل",
      description_ar: "مناسب للبرامج العامة: مستندات، استعلام أمني، اختبارات، مقابلتان، قرار نهائي.",
      build: buildIndividual
    },
    plp_jplp: {
      label_ar: "PLP / JPLP - مقابلة 10 محاور",
      description_ar: "سيناريو مختصر يستخدم نموذج مقابلة من 10 محاور مع التوصية النهائية.",
      build: buildPlpJplp
    },
    executive: {
      label_ar: "تنفيذي / مصريون بالخارج - 15 محوراً",
      description_ar: "سيناريو يستخدم نموذج مقابلة مفصل من 15 محوراً وتقييم قبلي.",
      build: buildExecutive
    },
    youth: {
      label_ar: "برامج الشباب - 10 محاور",
      description_ar: "سيناريو مقابلة موجه للشباب مع محاور السلوك والتعاون والتعبير.",
      build: buildYouth
    },
    nominee: {
      label_ar: "ترشيحات رسمية - بدون مقابلات",
      description_ar: "للمرشحين من جهة رسمية: مطابقة الترشيح، مستندات، استعلام، قرار نهائي.",
      build: buildNominee
    }
  };

  window.NTAAdmissionScenarioTemplates = {
    commonFive: commonFive,
    adultTen: adultTen,
    executiveFifteen: executiveFifteen,
    youthTen: youthTen,
    templates: templates,
    build: function (key) {
      var template = templates[key] || templates.individual_default;
      return template.build();
    },
    getTemplateOptions: function () {
      return Object.keys(templates).map(function (key) {
        return { key: key, label_ar: templates[key].label_ar, description_ar: templates[key].description_ar };
      });
    }
  };
})();
