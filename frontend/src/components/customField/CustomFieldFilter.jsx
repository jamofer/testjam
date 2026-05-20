import { useTranslation } from "react-i18next"
import { Input } from "../ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"

const ANY = "any"
const SELECT_TYPES = ["single_select", "multi_select"]

export function CustomFieldFilter({
  definitions,
  fieldKey,
  fieldValue,
  onFieldKeyChange,
  onFieldValueChange,
  selectedDefinition,
}) {
  const { t } = useTranslation("customFields")
  return (
    <div className="flex items-center gap-2">
      <Select value={fieldKey} onValueChange={onFieldKeyChange}>
        <SelectTrigger className="h-9 w-44" aria-label={t("filter.label")}>
          <SelectValue placeholder={t("filter.fieldPlaceholder")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ANY}>{t("filter.fieldPlaceholder")}</SelectItem>
          {definitions.map(definition => (
            <SelectItem key={definition.id} value={definition.key}>
              {definition.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {selectedDefinition && (
        <ValueControl
          definition={selectedDefinition}
          value={fieldValue}
          onChange={onFieldValueChange}
        />
      )}
    </div>
  )
}

function ValueControl({ definition, value, onChange }) {
  const { t } = useTranslation("customFields")
  if (SELECT_TYPES.includes(definition.type)) {
    return (
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="h-9 w-44">
          <SelectValue placeholder={t("filter.valuePlaceholder")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="any">{t("filter.any")}</SelectItem>
          {(definition.options || []).map(option => (
            <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    )
  }
  if (definition.type === "bool") {
    return (
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="h-9 w-32">
          <SelectValue placeholder={t("filter.valuePlaceholder")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="any">{t("filter.any")}</SelectItem>
          <SelectItem value="true">True</SelectItem>
          <SelectItem value="false">False</SelectItem>
        </SelectContent>
      </Select>
    )
  }
  return (
    <Input
      className="h-9 w-44"
      placeholder={t("filter.valuePlaceholder")}
      value={value === "any" ? "" : value}
      onChange={event => onChange(event.target.value || "any")}
    />
  )
}
