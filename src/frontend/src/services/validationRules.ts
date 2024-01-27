export function requiredRule(val: string) {
  return (val && val.length > 0) || "This field is required"
}