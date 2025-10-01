import { StyleSheet } from 'react-native';

export const colors = {
  primary: '#059669',
  primaryLight: '#6ee7b7',
  primaryPastel: '#d1fae5',
  primaryDark: '#065f46',
  secondary: '#047857',
  
  background: '#ffffff',
  surface: '#f9fafb',
  border: '#e5e7eb',
  borderDark: '#d1d5db',
  
  text: '#374151',
  textLight: '#6b7280',
  textLighter: '#9ca3af',
  
  error: '#dc2626',
  errorLight: '#fee2e2',
  
  warning: '#fbbf24',
  
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayDark: 'rgba(0, 0, 0, 0.7)',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  full: 9999,
};

export const fontSize = {
  text: 16,      // Body text, labels, buttons
  subheading: 20, // Section titles, card headers
  title: 30,      // Page titles
};

export const fonts = {
  light: 'NotoSerifGurmukhi-Light',
  medium: 'NotoSerifGurmukhi-Medium',
  semiBold: 'NotoSerifGurmukhi-SemiBold',
  extraBold: 'NotoSerifGurmukhi-ExtraBold',
  black: 'NotoSerifGurmukhi-Black', 
};

export const styles = StyleSheet.create({
  // Container styles
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  tabContent: {
    flex: 1,
    backgroundColor: colors.background,
  },
  
  // Header styles
  header: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.xl,
    paddingBottom: spacing.xl,
    backgroundColor: colors.background,
  },
  headerTitle: {
    fontSize: fontSize.title,
    fontFamily: fonts.extraBold,
    color: colors.primaryDark,
  },

  // Tab bar styles
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.background,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingBottom: spacing.xl,
    paddingTop: spacing.md,
    paddingHorizontal: spacing.xl,
    justifyContent: 'center',
    gap: spacing.xxxl,
  },
  tabButton: {
    backgroundColor: '#f3f4f6',
    borderRadius: borderRadius.xl,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    minWidth: 100,
  },
  tabButtonActive: {
    backgroundColor: colors.primaryLight,
  },
  tabButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLighter,
  },
  tabButtonTextActive: {
    fontFamily: fonts.semiBold,
    color: colors.primaryDark,
  },
  tabButtonIcon: {
  marginBottom: 2,
  },
  
  // Filter styles
  filterContainerWrapper: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  filterScroll: {
    maxWidth: 400,
  },
  filterContentContainer: {
    paddingHorizontal: spacing.xl,
  },
  filterChip: {
    backgroundColor: '#f3f4f6',
    borderRadius: borderRadius.xl,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    marginRight: spacing.sm,
  },
  filterChipActive: {
    backgroundColor: colors.primaryLight,
  },
  filterChipText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
  },
  filterChipTextActive: {
    fontFamily: fonts.semiBold,
    color: colors.primaryDark,
  },
  
  // Item grid styles
  itemsScroll: {
    flex: 1,
    paddingHorizontal: spacing.xl,
  },
  itemsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    paddingBottom: 100,
  },
  itemCard: {
    //width: '31%',
    aspectRatio: 0.75,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
    marginRight: '3.5%',
    borderWidth: 1,
    borderColor: colors.borderDark,
    padding: spacing.sm,
  },
  itemImage: {
    width: '100%',
    height: '100%',
  },
  
  // Loading styles
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: colors.overlayDark,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  loadingModal: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.xl,
    padding: 40,
    alignItems: 'center',
    minWidth: 250,
  },
  loadingText: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.text,
    marginTop: spacing.lg,
    textAlign: 'center',
  },
  loadingSubtext: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
  
  // FAB styles
  fab: {
    position: 'absolute',
    right: spacing.xl,
    bottom: 90,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  fabText: {
    fontSize: 32,
    fontFamily: fonts.semiBold,
    color: colors.primaryDark,
  },
  
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: colors.overlay,
    justifyContent: 'flex-end',
  },
  
  // Item modal styles
  itemModal: {
    backgroundColor: colors.background,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    paddingTop: spacing.xl,
    paddingBottom: 40,
    maxHeight: '85%',
  },
  itemModalImage: {
    width: '100%',
    height: 300,
    marginBottom: spacing.xl,
  },
  descriptionSection: {
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xl,
    alignItems: 'center',
  },
  descriptionHeader: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.text,
    marginBottom: spacing.lg,
    textAlign: 'center',
  },
  featuresList: {
    gap: spacing.md,
    width: '100%',
    maxWidth: 300,
  },
  featureRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  featureLabel: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
  },
  featureValue: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.text,
    marginLeft: spacing.lg,
  },
  colorSwatch: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.borderDark,
    marginLeft: spacing.lg,
  },
  itemModalButtons: {
    flexDirection: 'row',
    paddingHorizontal: spacing.xl,
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  createOutfitButton: {
    flex: 1,
    backgroundColor: colors.primaryLight,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
  },
  createOutfitButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.primaryDark,
  },
  deleteButton: {
    flex: 1,
    backgroundColor: colors.errorLight,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
  },
  deleteButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.error,
  },
  closeModalButton: {
    marginHorizontal: spacing.xl,
    backgroundColor: '#f3f4f6',
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
  },
  closeModalButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
  },
  
  // Add item modal styles
  addModal: {
    backgroundColor: colors.background,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    padding: spacing.xxl,
    paddingBottom: 40,
  },
  addModalTitle: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.text,
    marginBottom: spacing.xl,
  },
  addModalLabel: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
    marginBottom: spacing.md,
  },
  categoryButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.xxl,
  },
  categoryButton: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    borderRadius: borderRadius.sm,
    padding: spacing.md,
    alignItems: 'center',
  },
  categoryButtonActive: {
    backgroundColor: colors.primaryLight,
  },
  categoryButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
  },
  categoryButtonTextActive: {
    fontFamily: fonts.semiBold,
    color: colors.primaryDark,
  },
  uploadButton: {
    backgroundColor: colors.primaryLight,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  uploadButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.primaryDark,
  },
  cancelButton: {
    backgroundColor: '#f3f4f6',
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  cancelButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
  },
  
  // Outfit styles
  generateSection: {
    flexDirection: 'row',
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xxl,
    gap: spacing.md,
  },
  generateButtonImproved: {
    flex: 1,
    backgroundColor: colors.primaryPastel,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.borderDark,
  },
  generateButtonIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  generateButtonIconText: {
    fontSize: 24,
  },
  generateButtonTextImproved: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.secondary,
    textAlign: 'center',
  },
  outfitLoadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  outfitLoadingText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
    marginTop: spacing.md,
  },
  currentOutfitSection: {
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.xxxl,
  },
  outfitImages: {
    gap: spacing.md,
    marginBottom: spacing.xxxl,
  },
  outfitImageContainer: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  outfitImage: {
    width: 240,
    height: 240,
  },
  matchScore: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.primary,
    textAlign: 'center',
    marginBottom: spacing.xxl,
  },
  ratingSection: {
    alignItems: 'center',
    marginTop: spacing.xxl,
  },
  ratingLabel: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.text,
    marginBottom: spacing.lg,
  },
  starButtons: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  starButton: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  starText: {
    fontSize: 50,
    color: colors.warning,
    marginBottom: spacing.lg,
  },
  emptyOutfitState: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLighter,
  },
  
  // Recent outfits styles
  recentSection: {
    paddingTop: spacing.xxxl,
    paddingBottom: 100,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    marginTop: spacing.xxxl,
  },
  recentSectionTitle: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.text,
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.xl,
  },
  recentCardsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 100,
    paddingHorizontal: spacing.xl,
  },
  recentOutfitCard: {
    width: 200,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: 10,
    borderWidth: 1,
    borderColor: colors.border,
  },
  recentOutfitImageContainer: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  recentOutfitImage: {
    width: 140,
    height: 140,
  },
  recentOutfitRating: {
    alignItems: 'center',
    marginTop: spacing.xs,
  },
  recentRatingStars: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.warning,
  },
  
  // Picker modal styles
  pickerModal: {
    backgroundColor: colors.background,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    paddingTop: spacing.xl,
    paddingBottom: 40,
    maxHeight: '85%',
  },
  pickerModalTitle: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.text,
    paddingHorizontal: spacing.xl,
    marginBottom: spacing.lg,
  },
  pickerScroll: {
    flex: 1,
    paddingHorizontal: spacing.xl,
  },
  pickerGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
  },
  pickerItem: {
    width: '31%',
    aspectRatio: 0.75,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
    marginRight: '3.5%',
    borderWidth: 1,
    borderColor: colors.borderDark,
    padding: spacing.sm,
  },
  pickerItemImage: {
    width: '100%',
    height: '100%',
  },
  closePickerButton: {
    marginHorizontal: spacing.xl,
    marginTop: spacing.lg,
    backgroundColor: '#f3f4f6',
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    alignItems: 'center',
  },
  closePickerButtonText: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
  },
  
  // Stats styles
  statsContent: {
    paddingHorizontal: spacing.xl,
    paddingBottom: 100,
  },
  statCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.xl,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statLabel: {
    fontSize: fontSize.text,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
    marginBottom: spacing.sm,
  },
  statValue: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.primary,
  },
  projectCredit: {
    marginTop: 40,
    alignItems: 'center',
  },
  projectCreditText: {
    fontSize: fontSize.subheading,
    fontFamily: fonts.semiBold,
    color: colors.textLight,
  },
});