; ModuleID = '/home/klee/tmp_ghost_4101f27a/ghost.bc'
source_filename = "/home/klee/tmp_ghost_4101f27a/ghost.c"
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
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !16, metadata !DIExpression()), !dbg !17
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !18, metadata !DIExpression()), !dbg !19
  %0 = load i8*, i8** %s.addr, align 8, !dbg !20
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !20
  %1 = load i8, i8* %arrayidx, align 1, !dbg !20
  %conv = sext i8 %1 to i32, !dbg !20
  %sub = sub nsw i32 %conv, 48, !dbg !21
  store i32 %sub, i32* %symvar, align 4, !dbg !19
  %call = call i32 (...) @assume_NL_start(), !dbg !22
  call void @llvm.dbg.declare(metadata double* %d, metadata !23, metadata !DIExpression()), !dbg !25
  %2 = load i32, i32* %symvar, align 4, !dbg !26
  %conv1 = sitofp i32 %2 to double, !dbg !26
  store double %conv1, double* %d, align 8, !dbg !25
  %call2 = call i32 (...) @assume_NL_stop(), !dbg !27
  %3 = load double, double* %d, align 8, !dbg !28
  %cmp = fcmp olt double 2.000000e+00, %3, !dbg !30
  %4 = load double, double* %d, align 8
  %cmp4 = fcmp olt double %4, 3.000000e+00
  %or.cond = select i1 %cmp, i1 %cmp4, i1 false, !dbg !31
  br i1 %or.cond, label %if.then, label %if.else, !dbg !31

if.then:                                          ; preds = %entry
  store i32 1, i32* %retval, align 4, !dbg !32
  br label %return, !dbg !32

if.else:                                          ; preds = %entry
  store i32 0, i32* %retval, align 4, !dbg !34
  br label %return, !dbg !34

return:                                           ; preds = %if.else, %if.then
  %5 = load i32, i32* %retval, align 4, !dbg !36
  ret i32 %5, !dbg !36
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

declare dso_local i32 @assume_NL_start(...) #2

declare dso_local i32 @assume_NL_stop(...) #2

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @main() #0 !dbg !37 {
entry:
  %retval = alloca i32, align 4
  %s = alloca [4 x i8], align 1
  store i32 0, i32* %retval, align 4
  call void @llvm.dbg.declare(metadata [4 x i8]* %s, metadata !40, metadata !DIExpression()), !dbg !44
  %arraydecay = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !45
  call void @klee_make_symbolic(i8* %arraydecay, i64 4, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0)), !dbg !46
  %arrayidx = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !47
  %0 = load i8, i8* %arrayidx, align 1, !dbg !47
  %conv = sext i8 %0 to i32, !dbg !47
  %cmp = icmp sge i32 %conv, 0, !dbg !48
  %conv1 = zext i1 %cmp to i32, !dbg !48
  %conv2 = sext i32 %conv1 to i64, !dbg !47
  call void @klee_assume(i64 %conv2), !dbg !49
  %arraydecay3 = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !50
  %call = call i32 @logic_bomb(i8* %arraydecay3), !dbg !51
  ret i32 0, !dbg !52
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #2

declare dso_local void @klee_assume(i64) #2

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!3, !4, !5, !6, !7}
!llvm.ident = !{!8}

!0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !1, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !2, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "/home/klee/tmp_ghost_4101f27a/ghost.c", directory: "/home/klee")
!2 = !{}
!3 = !{i32 7, !"Dwarf Version", i32 4}
!4 = !{i32 2, !"Debug Info Version", i32 3}
!5 = !{i32 1, !"wchar_size", i32 4}
!6 = !{i32 7, !"uwtable", i32 1}
!7 = !{i32 7, !"frame-pointer", i32 2}
!8 = !{!"clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)"}
!9 = distinct !DISubprogram(name: "logic_bomb", scope: !10, file: !10, line: 10, type: !11, scopeLine: 10, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!10 = !DIFile(filename: "tmp_ghost_4101f27a/ghost.c", directory: "/home/klee")
!11 = !DISubroutineType(types: !12)
!12 = !{!13, !14}
!13 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!14 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !15, size: 64)
!15 = !DIBasicType(name: "char", size: 8, encoding: DW_ATE_signed_char)
!16 = !DILocalVariable(name: "s", arg: 1, scope: !9, file: !10, line: 10, type: !14)
!17 = !DILocation(line: 10, column: 22, scope: !9)
!18 = !DILocalVariable(name: "symvar", scope: !9, file: !10, line: 11, type: !13)
!19 = !DILocation(line: 11, column: 9, scope: !9)
!20 = !DILocation(line: 11, column: 18, scope: !9)
!21 = !DILocation(line: 11, column: 23, scope: !9)
!22 = !DILocation(line: 12, column: 5, scope: !9)
!23 = !DILocalVariable(name: "d", scope: !9, file: !10, line: 13, type: !24)
!24 = !DIBasicType(name: "double", size: 64, encoding: DW_ATE_float)
!25 = !DILocation(line: 13, column: 12, scope: !9)
!26 = !DILocation(line: 13, column: 16, scope: !9)
!27 = !DILocation(line: 14, column: 5, scope: !9)
!28 = !DILocation(line: 15, column: 12, scope: !29)
!29 = distinct !DILexicalBlock(scope: !9, file: !10, line: 15, column: 8)
!30 = !DILocation(line: 15, column: 10, scope: !29)
!31 = !DILocation(line: 15, column: 14, scope: !29)
!32 = !DILocation(line: 16, column: 9, scope: !33)
!33 = distinct !DILexicalBlock(scope: !29, file: !10, line: 15, column: 23)
!34 = !DILocation(line: 18, column: 9, scope: !35)
!35 = distinct !DILexicalBlock(scope: !29, file: !10, line: 17, column: 10)
!36 = !DILocation(line: 20, column: 1, scope: !9)
!37 = distinct !DISubprogram(name: "main", scope: !10, file: !10, line: 22, type: !38, scopeLine: 22, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!38 = !DISubroutineType(types: !39)
!39 = !{!13}
!40 = !DILocalVariable(name: "s", scope: !37, file: !10, line: 23, type: !41)
!41 = !DICompositeType(tag: DW_TAG_array_type, baseType: !15, size: 32, elements: !42)
!42 = !{!43}
!43 = !DISubrange(count: 4)
!44 = !DILocation(line: 23, column: 10, scope: !37)
!45 = !DILocation(line: 24, column: 24, scope: !37)
!46 = !DILocation(line: 24, column: 5, scope: !37)
!47 = !DILocation(line: 26, column: 17, scope: !37)
!48 = !DILocation(line: 26, column: 22, scope: !37)
!49 = !DILocation(line: 26, column: 5, scope: !37)
!50 = !DILocation(line: 27, column: 16, scope: !37)
!51 = !DILocation(line: 27, column: 5, scope: !37)
!52 = !DILocation(line: 28, column: 5, scope: !37)
