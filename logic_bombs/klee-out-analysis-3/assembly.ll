; ModuleID = 'ln_ef_l2/ln_ef_l2_klee.bc'
source_filename = "ln_ef_l2/ln_ef_l2_klee.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str = private unnamed_addr constant [2 x i8] c"s\00", align 1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @logic_bomb(i8* %s) #0 !dbg !9 {
entry:
  %retval = alloca i32, align 4
  %s.addr = alloca i8*, align 8
  %symvar = alloca i32, align 4
  %d = alloca double, align 8
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !15, metadata !DIExpression()), !dbg !16
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !17, metadata !DIExpression()), !dbg !18
  %0 = load i8*, i8** %s.addr, align 8, !dbg !19
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !19
  %1 = load i8, i8* %arrayidx, align 1, !dbg !19
  %conv = sext i8 %1 to i32, !dbg !19
  %sub = sub nsw i32 %conv, 48, !dbg !20
  store i32 %sub, i32* %symvar, align 4, !dbg !18
  call void @llvm.dbg.declare(metadata double* %d, metadata !21, metadata !DIExpression()), !dbg !23
  %2 = load i32, i32* %symvar, align 4, !dbg !24
  %conv1 = sitofp i32 %2 to double, !dbg !24
  %call = call double @log(double %conv1) #4, !dbg !25
  store double %call, double* %d, align 8, !dbg !23
  %3 = load double, double* %d, align 8, !dbg !26
  %cmp = fcmp olt double 2.000000e+00, %3, !dbg !28
  %4 = load double, double* %d, align 8
  %cmp3 = fcmp olt double %4, 3.000000e+00
  %or.cond = select i1 %cmp, i1 %cmp3, i1 false, !dbg !29
  br i1 %or.cond, label %if.then, label %if.else, !dbg !29

if.then:                                          ; preds = %entry
  store i32 1, i32* %retval, align 4, !dbg !30
  br label %return, !dbg !30

if.else:                                          ; preds = %entry
  store i32 0, i32* %retval, align 4, !dbg !32
  br label %return, !dbg !32

return:                                           ; preds = %if.else, %if.then
  %5 = load i32, i32* %retval, align 4, !dbg !34
  ret i32 %5, !dbg !34
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

; Function Attrs: nounwind
declare dso_local double @log(double) #2

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main(i32 %argc, i8** %argv) #0 !dbg !35 {
entry:
  %retval = alloca i32, align 4
  %argc.addr = alloca i32, align 4
  %argv.addr = alloca i8**, align 8
  %s = alloca [5 x i8], align 1
  store i32 0, i32* %retval, align 4
  store i32 %argc, i32* %argc.addr, align 4
  call void @llvm.dbg.declare(metadata i32* %argc.addr, metadata !39, metadata !DIExpression()), !dbg !40
  store i8** %argv, i8*** %argv.addr, align 8
  call void @llvm.dbg.declare(metadata i8*** %argv.addr, metadata !41, metadata !DIExpression()), !dbg !42
  call void @llvm.dbg.declare(metadata [5 x i8]* %s, metadata !43, metadata !DIExpression()), !dbg !47
  %0 = bitcast [5 x i8]* %s to i8*, !dbg !48
  call void @klee_make_symbolic(i8* %0, i64 5, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0)), !dbg !49
  %arrayidx = getelementptr inbounds [5 x i8], [5 x i8]* %s, i64 0, i64 4, !dbg !50
  %1 = load i8, i8* %arrayidx, align 1, !dbg !50
  %conv = sext i8 %1 to i32, !dbg !50
  %cmp = icmp eq i32 %conv, 0, !dbg !51
  %conv1 = zext i1 %cmp to i32, !dbg !51
  %conv2 = sext i32 %conv1 to i64, !dbg !50
  call void @klee_assume(i64 %conv2), !dbg !52
  %arraydecay = getelementptr inbounds [5 x i8], [5 x i8]* %s, i64 0, i64 0, !dbg !53
  %call = call i32 @logic_bomb(i8* %arraydecay), !dbg !54
  ret i32 %call, !dbg !55
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #3

declare dso_local void @klee_assume(i64) #3

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { nounwind }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!3, !4, !5, !6, !7}
!llvm.ident = !{!8}

!0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !1, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !2, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "ln_ef_l2/ln_ef_l2_klee.c", directory: "/home/klee")
!2 = !{}
!3 = !{i32 7, !"Dwarf Version", i32 4}
!4 = !{i32 2, !"Debug Info Version", i32 3}
!5 = !{i32 1, !"wchar_size", i32 4}
!6 = !{i32 7, !"uwtable", i32 1}
!7 = !{i32 7, !"frame-pointer", i32 2}
!8 = !{!"clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)"}
!9 = distinct !DISubprogram(name: "logic_bomb", scope: !1, file: !1, line: 9, type: !10, scopeLine: 9, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!10 = !DISubroutineType(types: !11)
!11 = !{!12, !13}
!12 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!13 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !14, size: 64)
!14 = !DIBasicType(name: "char", size: 8, encoding: DW_ATE_signed_char)
!15 = !DILocalVariable(name: "s", arg: 1, scope: !9, file: !1, line: 9, type: !13)
!16 = !DILocation(line: 9, column: 22, scope: !9)
!17 = !DILocalVariable(name: "symvar", scope: !9, file: !1, line: 10, type: !12)
!18 = !DILocation(line: 10, column: 9, scope: !9)
!19 = !DILocation(line: 10, column: 18, scope: !9)
!20 = !DILocation(line: 10, column: 23, scope: !9)
!21 = !DILocalVariable(name: "d", scope: !9, file: !1, line: 12, type: !22)
!22 = !DIBasicType(name: "double", size: 64, encoding: DW_ATE_float)
!23 = !DILocation(line: 12, column: 12, scope: !9)
!24 = !DILocation(line: 12, column: 20, scope: !9)
!25 = !DILocation(line: 12, column: 16, scope: !9)
!26 = !DILocation(line: 14, column: 12, scope: !27)
!27 = distinct !DILexicalBlock(scope: !9, file: !1, line: 14, column: 8)
!28 = !DILocation(line: 14, column: 10, scope: !27)
!29 = !DILocation(line: 14, column: 14, scope: !27)
!30 = !DILocation(line: 15, column: 9, scope: !31)
!31 = distinct !DILexicalBlock(scope: !27, file: !1, line: 14, column: 23)
!32 = !DILocation(line: 17, column: 9, scope: !33)
!33 = distinct !DILexicalBlock(scope: !27, file: !1, line: 16, column: 10)
!34 = !DILocation(line: 19, column: 1, scope: !9)
!35 = distinct !DISubprogram(name: "main", scope: !1, file: !1, line: 21, type: !36, scopeLine: 21, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!36 = !DISubroutineType(types: !37)
!37 = !{!12, !12, !38}
!38 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !13, size: 64)
!39 = !DILocalVariable(name: "argc", arg: 1, scope: !35, file: !1, line: 21, type: !12)
!40 = !DILocation(line: 21, column: 14, scope: !35)
!41 = !DILocalVariable(name: "argv", arg: 2, scope: !35, file: !1, line: 21, type: !38)
!42 = !DILocation(line: 21, column: 27, scope: !35)
!43 = !DILocalVariable(name: "s", scope: !35, file: !1, line: 22, type: !44)
!44 = !DICompositeType(tag: DW_TAG_array_type, baseType: !14, size: 40, elements: !45)
!45 = !{!46}
!46 = !DISubrange(count: 5)
!47 = !DILocation(line: 22, column: 6, scope: !35)
!48 = !DILocation(line: 23, column: 20, scope: !35)
!49 = !DILocation(line: 23, column: 1, scope: !35)
!50 = !DILocation(line: 24, column: 13, scope: !35)
!51 = !DILocation(line: 24, column: 17, scope: !35)
!52 = !DILocation(line: 24, column: 1, scope: !35)
!53 = !DILocation(line: 25, column: 19, scope: !35)
!54 = !DILocation(line: 25, column: 8, scope: !35)
!55 = !DILocation(line: 25, column: 1, scope: !35)
