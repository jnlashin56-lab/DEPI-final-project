# Data Audit

Generated from the current CSV files in the project workspace.

| Dataset | Rows | Missing primary names | Duplicate primary names | Missing selected price |
|---|---:|---:|---:|---:|
| English places | 1258 | 0 | 44 | 1184 |
| Arabic places | 1258 | 0 | 44 | 1184 |
| English ticket prices | 166 | 0 | 0 | 0 |
| Arabic ticket prices | 166 | 0 | 0 | 0 |

## Columns

### English places

name, latitude, longitude, category, description, place_id, price_egp

### Arabic places

الاسم, خط العرض, خط الطول, التصنيف, الوصف, معرف المكان, سعر الدخول (جنيه)

### English ticket prices

site_name, governorate, heritage_type, egyptian_egp, egyptian_student_egp, foreign_egp, foreign_student_egp, visiting_hours

### Arabic ticket prices

اسم الموقع, المحافظة, تصنيف الأثر, سعر المصري (جنيه), سعر الطالب المصري (جنيه), سعر الأجنبي (جنيه), سعر الطالب الأجنبي (جنيه), مواعيد الزيارة

## Step 1 decision

Use the English places file as the backend-friendly v1 source of truth, and load the matching Arabic places file alongside it for bilingual display fields. Both places files now contain the same 1,258 rows.
