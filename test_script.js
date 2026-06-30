
      (function () {
        var session = {};
        try {
          session = JSON.parse(sessionStorage.getItem("ntaTrainee") || "{}");
        } catch (e) {}
        if (session.role !== "admission_manager") {
          window.location.href = "index.html";
          return;
        }

        var STAGES = [
          { id: 0, label: "الكل" },
          { id: 1, label: "الفرز الإلكتروني" },
          { id: 2, label: "الاستعلام الأمني" },
          { id: 3, label: "الاختبار النفسي" },
          { id: 4, label: "اختبارات المعلومات واللغة العربية" },
          { id: 5, label: "المقابلة الأولى" },
          { id: 6, label: "المقابلة الثانية" },
        ];

        var trainees = [];
        var filtered = [];
        var activeStage = 0;
        var currentView = "cards";
        var currentPage = 1;
        var pageSize = 12;
        var isLoading = true;

        /* ── Stage pills ── */
        function renderPills() {
          var el = document.getElementById("auStagePills");
          el.innerHTML = STAGES.map(function (s) {
            var count = trainees.filter(function(t) {
              return (s.id === 0 || t.stage === s.id) && t.status !== 'rejected';
            }).length;
            
            return (
              '<button class="au-stage-pill' +
              (activeStage === s.id ? " active" : "") +
              '" onclick="selectStage(' +
              s.id +
              ')">' +
              s.label + ' (' + count + ')' +
              "</button>"
            );
          }).join("");
        }
        window.selectStage = function (id) {
          activeStage = id;
          currentPage = 1;
          renderPills();
          applyFilters();
          render();
        };

        /* ── Filters ── */
        function applyFilters() {
          var q = (document.getElementById("auSearch").value || "")
            .trim()
            .toLowerCase();
          
          // Show active and pending candidates; exclude rejected
          var list = trainees.filter(function(t) {
            return t.status !== 'rejected';
          });

          if (activeStage)
            list = list.filter(function (t) {
              return t.stage === activeStage;
            });
          if (q)
            list = list.filter(function (t) {
              return (
                (t.name || "").toLowerCase().indexOf(q) >= 0 ||
                (t.email || "").toLowerCase().indexOf(q) >= 0
              );
            });
          filtered = list;
          var title = activeStage
            ? STAGES.find(function (s) {
                return s.id === activeStage;
              }).label
            : "جميع المرشحين";
          document.getElementById("auSectionTitle").textContent = title;
          document.getElementById("auCount").textContent = filtered.length;
        }

        /* ── Build card ── */
        function buildCard(t, idx) {
          var prog = t.progress_percentage || 10;
          var initials = (t.name || "؟")
            .split(" ")
            .slice(0, 2)
            .map(function (w) {
              return w.charAt(0);
            })
            .join("");
          return (
            '<div class="au-card" data-stage="' +
            t.stage +
            '" style="animation-delay:' +
            idx * 0.05 +
            's">' +
            '<div class="au-card__img-wrap">' +
            '<img src="' +
            t.image +
            '" alt="" class="au-card__img" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">' +
            '<div class="au-card__img-placeholder" style="display:none">' +
            initials +
            "</div>" +
            '<span class="au-card__stage-badge">المرحلة ' +
            t.stage +
            "</span>" +
            "</div>" +
            '<div class="au-card__body">' +
            '<div class="au-card__name-row">' +
            '<h3 class="au-card__name">' +
            t.name +
            "</h3>" +
            '<span class="au-card__cat-badge">' +
            (t.category || "عام") +
            "</span>" +
            "</div>" +
            '<p class="au-card__meta"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>' +
            (t.education || "—") +
            " · " +
            (t.age || "—") +
            " سنة</p>" +
            '<div class="au-card__progress-wrap">' +
            '<div class="au-card__progress-label"><span>التقدم في الخط</span><span>' +
            prog +
            "%</span></div>" +
            '<div class="au-card__progress-bar"><div class="au-card__progress-fill" style="width:' +
            prog +
            '%"></div></div>' +
            "</div>" +
            '<a href="admin-profile.html?id=' +
            t.id +
            '&from=applicants" class="au-card__btn">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' +
            "إدارة الملف الشخصي</a>" +
            "</div></div>"
          );
        }

        /* ── Build table row ── */
        function buildRow(t, i) {
          var initials = (t.name || "؟")
            .split(" ")
            .slice(0, 2)
            .map(function (w) {
              return w.charAt(0);
            })
            .join("");
          var stageLabel =
            (
              STAGES.find(function (s) {
                return s.id === t.stage;
              }) || {}
            ).label || "—";
          return (
            "<tr onclick=\"window.location.href='admin-profile.html?id=" +
            t.id +
            "&from=applicants'\">" +
            "<td>" +
            i +
            "</td>" +
            '<td><div class="au-table__avatar">' +
            (t.image && t.image !== "null" ? '<img src="' + t.image + '" alt="" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">' : '') +
            '<span class="au-table__avatar-fallback" style="' + (t.image && t.image !== "null" ? 'display:none' : 'display:flex') + '">' +
            initials +
            "</span></div></td>" +
            '<td><span class="au-table__name">' +
            t.name +
            "</span></td>" +
            "<td>" +
            (t.category || "عام") +
            "</td>" +
            "<td>" +
            (t.age || "—") +
            "</td>" +
            "<td>" +
            (t.education || "—") +
            "</td>" +
            '<td><span class="au-stage-chip au-chip-' +
            t.stage +
            '">' +
            stageLabel +
            "</span></td>" +
            "</tr>"
          );
        }

        /* ── Render ── */
        function render() {
          if (isLoading) return;
          var total = filtered.length;
          var totalPages = Math.max(1, Math.ceil(total / pageSize));
          currentPage = Math.min(currentPage, totalPages);
          var start = (currentPage - 1) * pageSize;
          var slice = filtered.slice(start, start + pageSize);

          if (currentView === "cards") {
            document.getElementById("auViewTable").style.display = "none";
            document.getElementById("auViewCards").style.display = "";
            var grid = document.getElementById("auCardsGrid");
            grid.innerHTML =
              total === 0
                ? '<div class="au-empty">لا توجد نتائج.</div>'
                : slice
                    .map(function (t, i) {
                      return buildCard(t, i);
                    })
                    .join("");
            renderPagination(totalPages, "auPagination", "auPaginationInfo");
          } else {
            document.getElementById("auViewCards").style.display = "none";
            document.getElementById("auViewTable").style.display = "";
            var tbody = document.getElementById("auTableBody");
            tbody.innerHTML =
              total === 0
                ? '<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-subtle);">لا توجد نتائج</td></tr>'
                : slice
                    .map(function (t, i) {
                      return buildRow(t, start + i + 1);
                    })
                    .join("");
            renderPagination(totalPages, "auTablePagination", null);
          }
        }

        function renderPagination(totalPages, containerId, infoId) {
          var el = document.getElementById(containerId);
          if (!el) return;
          if (totalPages <= 1) {
            el.innerHTML = "";
            return;
          }
          var html =
            '<div style="display:flex;align-items:center;justify-content:center;gap:0.5rem;padding:1.25rem 0;">';
          html +=
            '<button class="courses-pagination__btn" ' +
            (currentPage === 1 ? "disabled" : "") +
            ' onclick="goPage(' +
            (currentPage - 1) +
            ')">‹ السابق</button>';
          html +=
            '<span style="font-size:0.82rem;color:var(--text-subtle);min-width:100px;text-align:center;">صفحة ' +
            currentPage +
            " من " +
            totalPages +
            "</span>";
          html +=
            '<button class="courses-pagination__btn" ' +
            (currentPage === totalPages ? "disabled" : "") +
            ' onclick="goPage(' +
            (currentPage + 1) +
            ')">التالي ›</button>';
          html += "</div>";
          el.innerHTML = html;
        }
        window.goPage = function (p) {
          currentPage = p;
          render();
        };

        /* ── Fetch ── */
        function fetchTrainees() {
          isLoading = true;
          // Check URL params for initial stage/status
          var urlParams = new URLSearchParams(window.location.search);
          var urlStage = urlParams.get("stage");
          var urlStatus = urlParams.get("status");
          if (urlStage) activeStage = parseInt(urlStage) || 0;
          if (urlStatus === "accepted") activeStage = 7;
          if (urlStatus === "rejected") {
            // Show only rejected candidates regardless of stage
            trainees = trainees.filter(function(t) { return t.status === 'rejected'; });
          }

          var url = "/api/admission/trainees";
          // Fetch all then filter client-side for pill flexibility
          window
            .authenticatedFetch(url)
            .then(function (res) {
              return res.json();
            })
            .then(function (data) {
              trainees = data
                .map(function (t) {
                  return {
                    id: t.id,
                    name: t.name,
                    email: t.email,
                    stage: t.stage || 1,
                    status: t.status,
                    category: t.category || "عام",
                    image: t.image_url || null,
                    age: t.age,
                    education: t.education,
                    progress_percentage: t.progress_percentage || 0
                  };
                  // Exclude stage 7 (المسجلين بالبرنامج) — they are shown in قائمة المتدربين
                })
                .filter(function (t) {
                  return t.stage !== 7;
                });
              isLoading = false;
              document.getElementById("auSkeleton").style.display = "none";
              document.getElementById("auCardsGrid").style.display = "";
              renderPills();
              applyFilters();
              render();
            })
            .catch(function (err) {
              console.error("Error fetching trainees:", err);
              isLoading = false;
              document.getElementById("auSkeleton").style.display = "none";
              document.getElementById("auCardsGrid").style.display = "";
              document.getElementById("auCardsGrid").innerHTML =
                '<div class="au-empty">حدث خطأ أثناء تحميل البيانات.</div>';
            });
        }

        /* ── Events ── */
        document
          .getElementById("auSearch")
          .addEventListener("input", function () {
            currentPage = 1;
            applyFilters();
            render();
          });
        document.querySelectorAll(".au-view-btn").forEach(function (btn) {
          btn.addEventListener("click", function () {
            currentView = this.getAttribute("data-view");
            document.querySelectorAll(".au-view-btn").forEach(function (b) {
              b.classList.remove("active");
            });
            this.classList.add("active");
            currentPage = 1;
            render();
          });
        });

        renderPills();
        fetchTrainees();
      })();
    