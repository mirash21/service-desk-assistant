"""
Quality Indicator Component - Display validation results
"""

import streamlit as st


def show_validation_result(validation: dict):
    """Display validation results with visual indicators"""
    
    st.subheader("🔍 Результаты проверки")
    
    # Score indicator
    score = validation.get('score', 0)
    is_valid = validation.get('is_valid', False)
    
    # Create columns for score and status
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Display score with color coding
        if score >= 80:
            st.metric("Оценка качества", f"{score}/100", delta="✅ Хорошо")
        elif score >= 60:
            st.metric("Оценка качества", f"{score}/100", delta="⚠️ Удовлетворительно")
        else:
            st.metric("Оценка качества", f"{score}/100", delta="❌ Плохо", delta_color="inverse")
    
    with col2:
        if is_valid:
            st.success("✅ Документ соответствует стандартам качества")
        else:
            st.error("❌ Документ требует улучшений перед сохранением")
    
    # Issues (critical problems)
    issues = validation.get('issues', [])
    if issues:
        st.markdown("### 🔴 Критические проблемы")
        for issue in issues:
            st.error(f"- {issue}")
    
    # Warnings
    warnings = validation.get('warnings', [])
    if warnings:
        st.markdown("### 🟡 Предупреждения")
        for warning in warnings:
            st.warning(f"- {warning}")
    
    # Suggestions
    suggestions = validation.get('suggestions', [])
    if suggestions:
        st.markdown("### 💡 Рекомендации по улучшению")
        for suggestion in suggestions:
            st.info(f"- {suggestion}")
    
    # Auto-fixes available
    auto_fixes = validation.get('auto_fixes', {})
    if auto_fixes:
        st.markdown("### 🔧 Доступны автоматические исправления")
            
        for fix_type, fix_value in auto_fixes.items():
            with st.expander(f"**{fix_type.replace('_', ' ').title()}"):
                if isinstance(fix_value, list):
                    st.write(", ".join(fix_value))
                else:
                    st.write(fix_value)
                    
                st.caption(f"💡 Это будет автоматически добавлено при сохранении с включенным автоисправлением")
        
    # Summary recommendation
    st.divider()
        
    if is_valid:
        st.success("🎉 **Готово к сохранению!** Ваш документ соответствует всем требованиям качества.")
    elif score >= 60:
        st.warning("⚠️ **Почти готово!** Рассмотрите возможность устранения предупреждений перед сохранением.")
    else:
        st.error("🛑 **Требуется работа!** Пожалуйста, устраните критические проблемы перед сохранением.")
